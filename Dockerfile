FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim


WORKDIR /app/serverclear

COPY . .

EXPOSE 8080

# Forward SSH agent into build
RUN uv sync --locked --no-cache

CMD ["uv", "run", "-m", "src.main", "--host", "0.0.0.0", "--port" , "8000"]
