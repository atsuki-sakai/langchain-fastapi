#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"

# 1) venv の存在確認
if [ ! -d .venv ]; then
  echo "[dev] .venv not found. run scripts/setup.sh first" >&2
  exit 1
fi

# 2) activate
. .venv/bin/activate

# 3) 起動
exec uvicorn main:app --reload --host 0.0.0.0 --port "$PORT"