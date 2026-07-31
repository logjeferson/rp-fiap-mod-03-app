FROM golang:1.23-alpine3.22 AS builder
WORKDIR /app
RUN apk update && apk upgrade --no-cache
COPY . .
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

FROM alpine:latest
COPY --from=builder /app/main .
EXPOSE 8004
RUN apk add --no-cache curl
ENTRYPOINT ["/main"]