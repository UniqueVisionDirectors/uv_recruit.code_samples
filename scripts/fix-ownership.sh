#!/bin/sh
# コンテナ実行後に root 所有になったファイルを uid 1000 に戻す（Task 16 参照）。
# 通常は不要（compose.yaml で user: "1000:1000" / キャッシュ /tmp リダイレクト済み）。
# 一時的な docker run/docker compose run がホスト bind-mount に書き込んだ場合に使用。
set -eu
docker run --rm -v "$(git rev-parse --show-toplevel)":/mnt alpine \
  sh -c 'find /mnt -path /mnt/.git -prune -o -user root -exec chown 1000:1000 {} +'
echo "ownership reclaimed for uid 1000"
