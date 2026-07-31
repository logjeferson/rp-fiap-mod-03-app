FROM python:3.11.15-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11.15-slim
WORKDIR /app
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8005
CMD ["python", "app.py"]