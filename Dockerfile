FROM python:3.10-slim
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry
WORKDIR /app
COPY . .

# poetry.lock이 없으면 pyproject.toml만 보고 설치
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi || poetry lock --no-ansi && poetry install --no-interaction --no-ansi

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

