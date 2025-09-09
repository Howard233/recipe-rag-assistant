FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI with uv + uvicorn
CMD ["uv", "run", "uvicorn", "recipe_assistant.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
