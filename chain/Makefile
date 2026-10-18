.PHONY: build clean test localnet lint proto-gen

GO ?= go
BIN ?= drpd

proto-gen:
	bash scripts/protocgen.sh

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

