
FROM python:3.10-slim
RUN apt-get update && apt-get install -y curl
RUN pip install --no-cache-dir poetry
WORKDIR /app
COPY . .
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 