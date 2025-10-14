# anomaly-detection-server

### Setup locally

```bash
# copy .env.example to .env
cp .env.example .env
```

```bash
docker compose --file docker-compose-local.yml up
```


### Load data

```bash
docker exec -it anomaly-detector-server sh
```

```bash
uv run python load_data.py
```

