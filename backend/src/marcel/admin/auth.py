from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import argon2
import jwt
from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request as StarletteRequest

from marcel.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY
from marcel.database import get_db
from marcel.models import AdminUser

PASSWORD_HASHER = PasswordHasher()

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials. Try to login again.",
    headers={"WWW-Authenticate": "Bearer"},
)

router = APIRouter()


class AdminUserRead(BaseModel):
    username: str


class OAuth2PasswordBearerFromCookie(OAuth2PasswordBearer):
    """
    Retrieve JWT access token from cookie rather than Authentication header.
    Based on: https://github.com/fastapi/fastapi/discussions/9142
    """

    async def __call__(self, request: StarletteRequest) -> Optional[str]:
        authorization = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise CREDENTIALS_EXCEPTION
            else:
                return None

        return param


oauth2_scheme = OAuth2PasswordBearerFromCookie(tokenUrl="/admin/login")


def hash_password(plain_password: str) -> str:
    return PASSWORD_HASHER.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(hashed_password, plain_password)
    except argon2.exceptions.VerifyMismatchError:
        return False


def get_user(db: Session, username: str) -> AdminUser | None:
    return db.execute(
        select(AdminUser).where(AdminUser.username == username)
    ).scalar_one_or_none()


def set_password_hash_for_user(db: Session, username: str, hashed_password: str):
    user = get_user(db, username)
    if user:
        user.hashed_password = hashed_password
        db.commit()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    # Now that we have the cleartext password,
    # check the hash's parameters and if outdated,
    # rehash the user's password in the database.
    # https://argon2-cffi.readthedocs.io/en/stable/howto.html
    if PASSWORD_HASHER.check_needs_rehash(user.hashed_password):
        set_password_hash_for_user(db, username, PASSWORD_HASHER.hash(password))

    return user


def create_token(
    username: str,
    expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
):
    expire = datetime.now(timezone.utc) + expires_delta
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> str:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"]).get("sub")
    except InvalidTokenError:
        raise CREDENTIALS_EXCEPTION


async def get_current_admin_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> AdminUser:
    username = decode_token(token)
    if username is None:
        raise CREDENTIALS_EXCEPTION
    user = get_user(db, username)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


@router.post("/login", response_model=AdminUserRead)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token(user.username)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES,  # Maximum age in seconds
        httponly=True,  # Prevent JavaScript from acessing the cookie
        samesite="strict",  # Only send cookies with requests from same origin
        secure=True,  # Only send cookie on https requests
    )

    return user


@router.post("/logout")
async def logout(response: Response, user: AdminUser = Depends(get_current_admin_user)):
    response.delete_cookie(
        key="access_token",
        # Options below are set identical to "set_cookie" in /login
        httponly=True,
        samesite="strict",
        secure=True,
    )


@router.get("/me", response_model=AdminUserRead)
async def me(user: AdminUser = Depends(get_current_admin_user)):
    return user
