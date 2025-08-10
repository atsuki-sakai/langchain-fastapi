# 開発用コマンド集

.PHONY: install dev clean venv

# 仮想環境の場所
VENV_DIR := .venv
PY := python3
PIP := $(VENV_DIR)/bin/pip
UVICORN := $(VENV_DIR)/bin/uvicorn

venv:
	$(PY) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/python -m pip install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

# 開発サーバー起動
# 使用: make dev [PORT=8000]
dev:
	@PORT=$${PORT:-8000}; \
	source $(VENV_DIR)/bin/activate; \
	$(UVICORN) main:app --reload --host 0.0.0.0 --port $$PORT

# 仮想環境削除
clean:
	rm -rf $(VENV_DIR) __pycache__ .pytest_cache