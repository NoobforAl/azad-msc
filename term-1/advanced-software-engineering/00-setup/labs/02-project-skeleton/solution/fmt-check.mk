
# Fails when Go or Python files are not formatted (CI uses this; `make fmt` fixes them).
fmt-check:
	test -z "$$(gofmt -l cmd internal)"
	ruff format --check analytics
