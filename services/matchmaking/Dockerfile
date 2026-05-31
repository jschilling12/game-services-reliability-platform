FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download && go mod tidy
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o matchmaking .

FROM gcr.io/distroless/static-debian12
WORKDIR /app
COPY --from=builder /app/matchmaking .
EXPOSE 8080
ENTRYPOINT ["/app/matchmaking"]
