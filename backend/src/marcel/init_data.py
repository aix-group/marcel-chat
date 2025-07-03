import argparse
import json
import logging
from typing import List

import haystack
from sqlalchemy import select
from sqlalchemy.orm import Session

from marcel.config import ADMINS_PATH, DATA_PATH, setup_logging
from marcel.database import engine
from marcel.experiments.data_loader import load_documents
from marcel.models import AdminUser, Document

logger = logging.getLogger(__name__)


def ingest_documents(db_session: Session, documents: List[haystack.Document]):
    try:
        existing = set(db_session.scalars(select(Document.fingerprint)).all())

        to_add = [
            Document(
                content=doc.content,
                url=doc.meta["url_raw"],
                title=doc.meta["title"],
                favicon=doc.meta["favicon"],
                fingerprint=doc.meta["fingerprint"],
            )
            for doc in documents
            if doc.meta["fingerprint"] not in existing
        ]

        if to_add:
            db_session.add_all(to_add)
            db_session.commit()

        logger.info("New: %d | Existing: %d", len(to_add), len(existing))

    except Exception:
        db_session.rollback()
        logger.exception("Error while ingesting documents")
        raise


def ingest_admin_users(db_session: Session, admins: List[dict[str, str]]):
    n_created = 0
    n_updated = 0

    for admin in admins:
        user = db_session.execute(
            select(AdminUser).where(AdminUser.username == admin["username"])
        ).scalar_one_or_none()
        if user:
            user.hashed_password = admin["hashed_password"]
            n_updated += 1
        else:
            user = AdminUser(**admin)
            n_created += 1
        db_session.add(user)
    db_session.commit()

    logger.info("New: %d | Updated: %d", n_created, n_updated)


def main(args):
    logger.info(f"Seeding: {args.data}")

    if args.data == "documents":
        documents = load_documents(DATA_PATH)
        with Session(engine) as session:
            ingest_documents(session, documents)

    if args.data == "admins":
        try:
            with open(ADMINS_PATH) as fin:
                admins = json.load(fin)
        except OSError:
            logger.warning(
                "Admin file not found. Make sure to set environment variable to insert/update admins (ADMINS_PATH=%s)",
                ADMINS_PATH,
            )
            admins = []

        with Session(engine) as session:
            ingest_admin_users(session, admins)

    logger.info("Done")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data",
        choices=["admins", "documents"],
        help="Choose data to seed.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    main(parse_arguments())
