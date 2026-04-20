.PHONY: build clean test localnet lint

GO ?= go
BIN ?= drpd

build:
	$(GO) build -o build/$(BIN) ./cmd/$(BIN)

test:
	$(GO) test ./... -count=1

clean:
	rm -rf build/

localnet:
	./scripts/localnet.sh

lint:
	@echo "No Go linter configured yet (add golangci-lint when desired)."

