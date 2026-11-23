#!/usr/bin/env bash
# bisect-test.sh: the "oracle" for `git bisect run`. Run it from the root of the repository.
#   exit 0   good: the code builds and the ordering test passes
#   exit 1   bad: the code builds and the ordering test fails
#   exit 125 cannot tell: the code does not build, so `git bisect` skips this commit
if ! go build ./... > /dev/null 2>&1; then
  echo "bisect-test: build fails, skipping this commit" >&2
  exit 125
fi
go test ./internal/catalog -run 'TestListIsSortedByID' -count=1 > /dev/null 2>&1
