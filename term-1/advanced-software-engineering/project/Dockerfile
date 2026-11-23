FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY cmd ./cmd
COPY internal ./internal
RUN CGO_ENABLED=0 go build -o /out/registration-api ./cmd/registration-api

FROM alpine:3.20
COPY --from=build /out/registration-api /usr/local/bin/registration-api
EXPOSE 8080
ENTRYPOINT ["registration-api"]
