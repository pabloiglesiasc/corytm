.PHONY: check check-all check-python check-frontend check-native clean

check: check-python check-frontend check-native

check-all: clean check

check-python:
	cd src/backend/core && uv run pytest
	cd src/backend/core && uv run pyright
	cd src/backend/core && uv run ruff check .
	cd src/backend/core && uv run ruff format --check .

check-frontend:
	cd src/frontend/desktop && npm ci
	cd src/frontend/desktop && npm run build
	cd src/frontend/desktop && npm run test
	cd src/frontend/desktop && npm run lint

check-native:
	cmake -S src/backend/audio -B src/backend/audio/build
	cmake --build src/backend/audio/build --config Release
	ctest --test-dir src/backend/audio/build --output-on-failure -C Release

clean:
	rm -rf src/backend/core/.venv
	rm -rf src/frontend/desktop/node_modules
	rm -rf src/backend/audio/build
