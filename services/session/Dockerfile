FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download && go mod tidy
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o session .

FROM gcr.io/distroless/static-debian12
WORKDIR /app
COPY --from=builder /app/session .
EXPOSE 8081
ENTRYPOINT ["/app/session"]
