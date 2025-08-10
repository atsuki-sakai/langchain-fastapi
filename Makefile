# 開発用コマンド集

.PHONY: install dev dev-prod clean venv test test-unit test-integration lint format check help migrate docker-up docker-down docker-logs docker-clean

# 仮想環境の場所
VENV_DIR := .venv
PY := python3
PIP := $(VENV_DIR)/bin/pip
UVICORN := $(VENV_DIR)/bin/uvicorn
PYTEST := $(VENV_DIR)/bin/pytest
BLACK := $(VENV_DIR)/bin/black
ISORT := $(VENV_DIR)/bin/isort
FLAKE8 := $(VENV_DIR)/bin/flake8

venv:
	$(PY) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/python -m pip install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt
	$(PIP) install black isort flake8

# 開発サーバー起動 (開発環境設定)
# 使用: make dev [PORT=8000]
dev:
	@PORT=$${PORT:-8000}; \
	export ENVIRONMENT=development; \
	source $(VENV_DIR)/bin/activate; \
	$(UVICORN) main:app --reload --host 0.0.0.0 --port $$PORT

# 本番環境設定でサーバー起動
# 使用: make dev-prod [PORT=8000]
dev-prod:
	@PORT=$${PORT:-8000}; \
	export ENVIRONMENT=production; \
	source $(VENV_DIR)/bin/activate; \
	$(UVICORN) main:app --host 0.0.0.0 --port $$PORT

# テスト実行
test:
	source $(VENV_DIR)/bin/activate; \
	$(PYTEST) -v

test-unit:
	source $(VENV_DIR)/bin/activate; \
	$(PYTEST) -v -m unit

test-integration:
	source $(VENV_DIR)/bin/activate; \
	$(PYTEST) -v -m integration

# コードフォーマット
format:
	source $(VENV_DIR)/bin/activate; \
	$(BLACK) app/ main.py; \
	$(ISORT) app/ main.py

# リント実行
lint:
	source $(VENV_DIR)/bin/activate; \
	$(FLAKE8) app/ main.py --max-line-length=88 --extend-ignore=E203,W503

# フォーマット・リント・テストを実行
check: format lint test

# データベースマイグレーション（開発環境）
migrate-dev:
	export ENVIRONMENT=development; \
	source $(VENV_DIR)/bin/activate; \
	python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"

# データベースマイグレーション（本番環境）
migrate-prod:
	export ENVIRONMENT=production; \
	source $(VENV_DIR)/bin/activate; \
	python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"

# Docker関連コマンド
docker-up:
	docker-compose up -d
	@echo "PostgreSQLが起動しました："
	@echo "  Database: http://localhost:5432"
	@echo "  pgAdmin: http://localhost:5050 (admin@fastapi.com / admin123)"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

# 仮想環境削除
clean:
	rm -rf $(VENV_DIR) __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete

# ヘルプ
help:
	@echo "利用可能なコマンド:"
	@echo ""
	@echo "📦 環境構築:"
	@echo "  venv         - 仮想環境作成"
	@echo "  install      - 依存関係インストール"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-up    - PostgreSQL起動 (localhost:5432)"
	@echo "  docker-down  - PostgreSQL停止"
	@echo "  docker-logs  - PostgreSQLログ表示"
	@echo "  docker-clean - Docker完全削除"
	@echo ""
	@echo "🚀 実行:"
	@echo "  dev          - 開発サーバー起動 (ローカルDB)"
	@echo "  dev-prod     - 本番設定サーバー起動 (リモートDB)"
	@echo ""
	@echo "🗄️ データベース:"
	@echo "  migrate-dev  - 開発環境DBマイグレーション"
	@echo "  migrate-prod - 本番環境DBマイグレーション"
	@echo ""
	@echo "🧪 テスト:"
	@echo "  test         - 全テスト実行"
	@echo "  test-unit    - 単体テスト実行"
	@echo "  test-integration - 統合テスト実行"
	@echo ""
	@echo "🔧 コード品質:"
	@echo "  format       - コードフォーマット"
	@echo "  lint         - リント実行"
	@echo "  check        - フォーマット・リント・テスト実行"
	@echo ""
	@echo "🧹 クリーンアップ:"
	@echo "  clean        - 仮想環境・キャッシュ削除"
	@echo "  help         - このヘルプ表示"