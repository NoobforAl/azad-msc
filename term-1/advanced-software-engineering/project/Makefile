# Course Registration Platform: build, test and lint (tag m0). Run from this folder.
.PHONY: test lint run build fmt check

test:
	go test ./...
	python -m unittest discover -s analytics/tests -v

lint:
	go vet ./...
	ruff check analytics

fmt:
	gofmt -w cmd internal
	ruff format analytics

run:
	go run ./cmd/registration-api

build:
	go build -o bin/registration-api ./cmd/registration-api

check: lint test
