#!/usr/bin/env bash
set -euo pipefail

# 日本語ログを出す
log() { echo "[setup] $1"; }

# 1) 仮想環境の作成
if [ ! -d .venv ]; then
  log "create venv"
  python3 -m venv .venv
fi

# 2) pip アップグレード
log "upgrade pip"
. .venv/bin/activate
python -m pip install --upgrade pip

# 3) 依存インストール
log "install requirements"
pip install -r requirements.txt

log "done"