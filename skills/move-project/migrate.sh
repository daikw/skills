#!/usr/bin/env bash
# Claude Code プロジェクト履歴マイグレーションスクリプト
# 使い方: bash migrate.sh <旧パス> <新パス>
# 例:     bash migrate.sh /old/path/project /new/path/project

set -euo pipefail

SRC_PATH="${1:-}"
DST_PATH="${2:-}"

if [ -z "$SRC_PATH" ] || [ -z "$DST_PATH" ]; then
  echo "Usage: $0 <src_path> <dst_path>"
  echo "  例: $0 /Users/me/old-project /Users/me/new-project"
  exit 1
fi

# 絶対パスに正規化（~ を展開）
SRC_PATH="${SRC_PATH/#\~/$HOME}"
DST_PATH="${DST_PATH/#\~/$HOME}"

SRC_KEY=$(echo "$SRC_PATH" | sed 's|/|-|g' | sed 's|\.|-|g')
DST_KEY=$(echo "$DST_PATH" | sed 's|/|-|g' | sed 's|\.|-|g')

PROJECTS_DIR="$HOME/.claude/projects"
SRC_DIR="$PROJECTS_DIR/$SRC_KEY"
DST_DIR="$PROJECTS_DIR/$DST_KEY"

echo "src: $SRC_PATH"
echo "dst: $DST_PATH"
echo ""

if [ ! -d "$SRC_DIR" ]; then
  echo "ERROR: 履歴ディレクトリが見つかりません: $SRC_DIR"
  exit 1
fi
if [ -d "$DST_DIR" ]; then
  echo "ERROR: 移動先が既に存在します: $DST_DIR"
  exit 1
fi

# BSD sed 対応: ] だけ第2パスで別途エスケープ
_escape_sed_pattern() {
  printf '%s' "$1" | sed 's/[.^$*\\[]/\\&/g' | sed 's/]/\\]/g'
}

D=$'\x01'  # パスに含まれない非印字文字をデリミタに使用

SRC_PATH_ESC=$(_escape_sed_pattern "$SRC_PATH")
SRC_KEY_ESC=$(_escape_sed_pattern "$SRC_KEY")

echo "履歴ディレクトリを移動中..."
mv "$SRC_DIR" "$DST_DIR"

echo "ファイル内のパスを更新中..."
file_count=0
skip_count=0

while IFS= read -r f; do
  if ! file "$f" | grep -qE 'text|JSON|ASCII'; then
    skip_count=$((skip_count + 1))
    continue
  fi

  # sed -i '' は mtime を更新するので退避・復元する
  mtime=$(stat -f "%m" "$f")

  # ファイルシステムパス形式（末尾アンカー: / か "）
  sed -i '' "s${D}${SRC_PATH_ESC}/${D}${DST_PATH}/${D}g" "$f"
  sed -i '' "s${D}${SRC_PATH_ESC}\"${D}${DST_PATH}\"${D}g" "$f"
  # Claude ディレクトリ名形式（/ → - 変換済み）
  sed -i '' "s${D}${SRC_KEY_ESC}/${D}${DST_KEY}/${D}g" "$f"
  sed -i '' "s${D}${SRC_KEY_ESC}\"${D}${DST_KEY}\"${D}g" "$f"

  # mtime を復元（/resume の時系列ソートを維持するため）
  touch -t "$(date -r "$mtime" "+%Y%m%d%H%M.%S")" "$f"

  file_count=$((file_count + 1))
done < <(find "$DST_DIR" -type f)

echo ""
echo "完了: $file_count ファイル更新、$skip_count ファイルスキップ（バイナリ）"
echo "OK: $SRC_PATH -> $DST_PATH"
