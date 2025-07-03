# Backend (`./backend`)
## Development
We use [pdm](https://github.com/pdm-project/pdm/) for dependency management.

```sh
pdm install
```

Start in dev mode (see: http://localhost:8000/docs)

```sh
pdm run dev
```

Admin users are automatically populated in prestart. To create an admin user/password, create `data/admins.json` with this content:

```json
[
  {
    "username": "firstname.lastname@uni-marburg.de",
    "hashed_password": "CHANGEME"
  }
]
```

where `hashed_password`:

```py
from argon2 import PasswordHasher
ph = PasswordHasher()
ph.hash("plainpasswordhere")
```

</details>

## Lint and format

```sh
pdm run lint
pdm run format
```
## Tests
```sh
pdm run test
```