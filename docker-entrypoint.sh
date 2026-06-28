#!/usr/bin/env bash
set -euo pipefail

# 依存を同期（バインドマウント後に実行され、.venv は volume 上に作られる）
uv sync

# DB マイグレーションを適用（migrations が存在する場合のみ）
if [ -f alembic.ini ]; then
  uv run alembic upgrade head
fi

exec "$@"
