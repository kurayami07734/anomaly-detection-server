FROM python:3.12-alpine

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN uv sync --frozen --no-cache

COPY . /app

EXPOSE 8000

CMD ["/app/.venv/bin/fastapi", "run", "src/main.py", "--port", "8000"]