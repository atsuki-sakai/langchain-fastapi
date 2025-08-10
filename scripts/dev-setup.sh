#!/usr/bin/env bash
set -euo pipefail

echo "🚀 FastAPI開発環境セットアップ開始..."

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[setup]${NC} $1"; }
info() { echo -e "${BLUE}[info]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC} $1"; }

# Dockerの確認
if ! command -v docker &> /dev/null; then
    warn "Dockerがインストールされていません"
    echo "https://docs.docker.com/get-docker/ からインストールしてください"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    warn "Docker Composeがインストールされていません"
    echo "https://docs.docker.com/compose/install/ からインストールしてください"
    exit 1
fi

# 1. 仮想環境とパッケージインストール
log "仮想環境作成とパッケージインストール"
make install

# 2. 環境変数ファイル作成
if [ ! -f .env.dev ]; then
    log ".env.devファイルが見つかりません"
    exit 1
fi

# 3. PostgreSQL起動
log "PostgreSQL (Docker) 起動中..."
make docker-up

# 4. データベースが起動するまで待機
log "データベース起動待機中..."
sleep 10

# 5. データベーステーブル作成
log "データベーステーブル作成"
make migrate-dev

log "✅ セットアップ完了！"
echo ""
info "次のコマンドで開発サーバーを起動してください："
info "  make dev"
echo ""
info "API確認URL："
info "  ヘルスチェック: http://localhost:8000/api/v1/health"
info "  APIドキュメント: http://localhost:8000/api/v1/docs"
info "  pgAdmin: http://localhost:5050 (admin@fastapi.com / admin123)"
echo ""
info "その他のコマンド："
info "  make help           - 全コマンド表示"
info "  make docker-logs    - PostgreSQLログ表示"
info "  make docker-down    - PostgreSQL停止"