# Docker Development

## Installation
Please follow [instruction](https://docs.docker.com/engine/install/)
## Usage 
Build from source
```sh
docker compose build
```

Start containers:

```sh
docker compose --env-file .env up
```

Ingest admin users. The container has to be on the same Docker network as the database.
The seed data is mounted as a volume.

```sh
docker run \
  --env-file .env \
  --network marcel_default \
  --mount type=bind,src=./data/seed,dst=/data/seed \
  python -m marcel.init_data admins

# Expected output (depending on content of admin.json)
2025-06-10 09:05:13,359 [MainProcess: 1] [INFO] __main__: Seeding: admins
2025-06-10 09:05:13,366 [MainProcess: 1] [INFO] __main__: New: 7 | Updated: 0
2025-06-10 09:05:13,366 [MainProcess: 1] [INFO] __main__: Done
```

Stop containers:

```sh
docker compose down
```

Cleanup:

```sh
docker volume rm marcel_data
```

