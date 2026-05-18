#!/usr/bin/env bash
# Codex CLI セッション履歴マイグレーションスクリプト
# 使い方: bash migrate-codex.sh [--check] <旧パス> <新パス>
# 例:     bash migrate-codex.sh /old/path/project /new/path/project
#         bash migrate-codex.sh --check /old/path/project /new/path/project
#
# Codex は ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl に日付ベースで保存する。
# ディレクトリ移動は不要で、各ファイルの session_meta.payload.cwd を更新するだけでよい。

set -euo pipefail

# --check フラグの処理
CHECK_ONLY=false
if [ "${1:-}" = "--check" ]; then
  CHECK_ONLY=true
  shift
fi

SRC_PATH="${1:-}"
DST_PATH="${2:-}"

if [ -z "$SRC_PATH" ] || [ -z "$DST_PATH" ]; then
  echo "Usage: $0 [--check] <src_path> <dst_path>"
  echo "  --check  移行対象の確認のみ行う（ファイルは変更しない）"
  echo "  例: $0 /Users/me/old-project /Users/me/new-project"
  exit 1
fi

# 絶対パスに正規化（~ を展開）
SRC_PATH="${SRC_PATH/#\~/$HOME}"
DST_PATH="${DST_PATH/#\~/$HOME}"

SESSIONS_DIR="$HOME/.codex/sessions"
CONFIG_FILE="$HOME/.codex/config.toml"

echo "src: $SRC_PATH"
echo "dst: $DST_PATH"
echo ""

# --- チェックフェーズ ---

if [ ! -d "$SESSIONS_DIR" ]; then
  echo "INFO: Codex セッションディレクトリが存在しません: $SESSIONS_DIR"
  echo "      → 移行不要（Codex の履歴はありません）"
  exit 0
fi

# session_meta.payload.cwd が一致するファイルを検索
# cwd は必ず1行目の session_meta に含まれる
echo "Codex セッションを検索中..."
matched_files=$(grep -rl "\"cwd\":\"$SRC_PATH\"" "$SESSIONS_DIR" 2>/dev/null || true)
matched_count=$(echo "$matched_files" | grep -c . 2>/dev/null || echo 0)

if [ "$matched_count" -eq 0 ] || [ -z "$matched_files" ]; then
  echo "INFO: 対象セッションが見つかりません（cwd: $SRC_PATH）"
  echo "      → 移行不要"
  # config.toml のチェックだけ行う
  if [ -f "$CONFIG_FILE" ] && grep -qF "$SRC_PATH" "$CONFIG_FILE" 2>/dev/null; then
    echo ""
    echo "NOTE: config.toml に旧パスの参照があります"
    grep -n "$SRC_PATH" "$CONFIG_FILE" | sed 's/^/  /'
    echo "      → 手動で確認してください: $CONFIG_FILE"
  fi
  exit 0
fi

echo "Codex セッション履歴:"
echo "  検索ディレクトリ: $SESSIONS_DIR"
echo "  対象セッション数: $matched_count ファイル"
echo ""
echo "$matched_files" | sed 's|.*/sessions/||' | sed 's/^/  /'

# config.toml チェック
config_hit=false
if [ -f "$CONFIG_FILE" ] && grep -qF "$SRC_PATH" "$CONFIG_FILE" 2>/dev/null; then
  config_hit=true
  echo ""
  echo "config.toml:"
  grep -n "$SRC_PATH" "$CONFIG_FILE" | sed 's/^/  /'
fi

$CHECK_ONLY && { echo ""; echo "→ '--check' モード: 変更は行いませんでした"; exit 0; }

# --- 実行フェーズ ---

# JSON 値として完全一致で置換（前方一致による誤置換を防ぐ）
# "cwd":"/old/path" → "cwd":"/new/path"
D=$'\x01'

echo ""
echo "セッションファイルを更新中..."
updated=0

echo "$matched_files" | while IFS= read -r f; do
  [ -z "$f" ] && continue

  mtime=$(stat -f "%m" "$f")

  # cwd の完全一致置換（JSON 文字列として境界を確定）
  sed -i '' "s${D}\"cwd\":\"${SRC_PATH}\"${D}\"cwd\":\"${DST_PATH}\"${D}g" "$f"
  # セッション内のその他のパス参照も更新（コスメティック）
  sed -i '' "s${D}${SRC_PATH}/${D}${DST_PATH}/${D}g" "$f"
  sed -i '' "s${D}${SRC_PATH}\"${D}${DST_PATH}\"${D}g" "$f"

  # mtime を復元（codex resume の表示順序を維持するため）
  touch -t "$(date -r "$mtime" "+%Y%m%d%H%M.%S")" "$f"

  updated=$((updated + 1))
done

# config.toml の更新
if $config_hit; then
  echo "config.toml を更新中..."
  mtime=$(stat -f "%m" "$CONFIG_FILE")
  sed -i '' "s${D}${SRC_PATH}${D}${DST_PATH}${D}g" "$CONFIG_FILE"
  touch -t "$(date -r "$mtime" "+%Y%m%d%H%M.%S")" "$CONFIG_FILE"
fi

echo ""
echo "完了: $matched_count セッション更新"
echo "OK: $SRC_PATH -> $DST_PATH"
