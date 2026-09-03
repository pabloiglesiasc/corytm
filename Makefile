.PHONY: check check-all check-python check-frontend check-desktop check-native check-transport clean

SCCACHE_INSTALLED := $(shell command -v sccache 2>/dev/null)

ifneq ($(SCCACHE_INSTALLED),)
ifeq ($(OS),Windows_NT)
CMAKE_CONFIGURE_FLAGS ?=
else
CMAKE_CONFIGURE_FLAGS ?= -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache
endif
RUSTC_WRAPPER ?= sccache
export RUSTC_WRAPPER
else
CMAKE_CONFIGURE_FLAGS ?=
endif

FRONTEND_DIR := src/frontend/desktop
FRONTEND_INSTALL_STAMP := $(FRONTEND_DIR)/node_modules/.install-stamp

check: check-python check-frontend check-native check-desktop check-transport

check-all: clean check

check-python:
	mkdir -p src/backend/core/src/corytm/generated
	cd src/backend/core && uv run python -m grpc_tools.protoc -I ../../schemas --python_out=src/corytm/generated --pyi_out=src/corytm/generated ../../schemas/proof.proto ../../schemas/project.proto ../../schemas/desktop.proto
	cd src/backend/core && uv run pytest -m "not transport and not live_llm"
	cd src/backend/core && uv run pyright
	cd src/backend/core && uv run ruff check .
	cd src/backend/core && uv run ruff format --check .

$(FRONTEND_INSTALL_STAMP): $(FRONTEND_DIR)/package-lock.json
	cd $(FRONTEND_DIR) && npm ci
	touch $(FRONTEND_INSTALL_STAMP)

check-frontend: $(FRONTEND_INSTALL_STAMP)
	cd $(FRONTEND_DIR) && npm run build
	cd $(FRONTEND_DIR) && npm run test
	cd $(FRONTEND_DIR) && npm run lint

check-desktop:
	cd src/frontend/desktop && npm run tauri build
	cd src/frontend/desktop/src-tauri && cargo test

check-native:
	cmake -S src/backend/audio -B src/backend/audio/build $(CMAKE_CONFIGURE_FLAGS)
	cmake --build src/backend/audio/build --config Release
	ctest --test-dir src/backend/audio/build --output-on-failure -C Release

check-transport:
	cd src/backend/core && uv run pytest -m transport

clean:
	rm -rf src/backend/core/.venv
	rm -rf src/backend/core/src/corytm/generated
	rm -rf src/frontend/desktop/node_modules
	rm -rf src/frontend/desktop/src-tauri/target
	rm -rf src/backend/audio/build
