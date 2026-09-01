FROM python:3.11.15-alpine AS builder
WORKDIR /app
RUN apk add --no-cache gcc musl-dev
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11.15-alpine
WORKDIR /app
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*
COPY . .
RUN adduser -D appuser && chown -R appuser /app
USER appuser
EXPOSE 8003
CMD ["python", "app.py"]