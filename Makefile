.PHONY: check check-all check-python check-frontend check-desktop check-native check-transport clean

CMAKE_CONFIGURE_FLAGS ?=

check: check-python check-frontend check-desktop check-native check-transport

check-all: clean check

check-python:
	mkdir -p src/backend/core/src/corytm/generated
	cd src/backend/core && uv run python -m grpc_tools.protoc -I ../../schemas --python_out=src/corytm/generated --pyi_out=src/corytm/generated ../../schemas/proof.proto ../../schemas/project.proto
	cd src/backend/core && uv run pytest -m "not transport"
	cd src/backend/core && uv run pyright
	cd src/backend/core && uv run ruff check .
	cd src/backend/core && uv run ruff format --check .

check-frontend:
	cd src/frontend/desktop && npm ci
	cd src/frontend/desktop && npm run build
	cd src/frontend/desktop && npm run test
	cd src/frontend/desktop && npm run lint

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
