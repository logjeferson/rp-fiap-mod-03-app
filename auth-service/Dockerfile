FROM golang:1.25-alpine AS builder
WORKDIR /app
RUN apk update && apk upgrade --no-cache
COPY . .
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

FROM scratch
COPY --from=builder /app/main .
EXPOSE 8001
ENTRYPOINT ["/main"]