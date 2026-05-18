#!/usr/bin/env bash
# Claude Code プロジェクト履歴マイグレーションスクリプト
# 使い方: bash migrate-claude.sh [--check] <旧パス> <新パス>
# 例:     bash migrate-claude.sh /old/path/project /new/path/project
#         bash migrate-claude.sh --check /old/path/project /new/path/project

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

SRC_KEY=$(echo "$SRC_PATH" | sed 's|/|-|g' | sed 's|\.|-|g')
DST_KEY=$(echo "$DST_PATH" | sed 's|/|-|g' | sed 's|\.|-|g')

PROJECTS_DIR="$HOME/.claude/projects"
SRC_DIR="$PROJECTS_DIR/$SRC_KEY"
DST_DIR="$PROJECTS_DIR/$DST_KEY"

echo "src: $SRC_PATH"
echo "dst: $DST_PATH"
echo ""

# --- チェックフェーズ ---

if [ ! -d "$SRC_DIR" ]; then
  echo "INFO: Claude Code 履歴ディレクトリが存在しません: $SRC_DIR"
  echo "      → 移行不要（このプロジェクトの Claude 履歴はありません）"
  exit 0
fi

file_count=$(find "$SRC_DIR" -type f | wc -l | tr -d ' ')
binary_count=$(find "$SRC_DIR" -type f | while IFS= read -r f; do
  file "$f" | grep -qE 'text|JSON|ASCII' || echo skip
done | wc -l | tr -d ' ')
text_count=$((file_count - binary_count))

echo "Claude Code 履歴:"
echo "  履歴ディレクトリ: $SRC_DIR"
echo "  総ファイル数:     $file_count"
echo "  更新対象:         $text_count ファイル"
echo "  スキップ(バイナリ): $binary_count ファイル"

if [ -d "$DST_DIR" ]; then
  echo ""
  echo "WARNING: 移動先ディレクトリが既に存在します: $DST_DIR"
  echo "         → 移行を実行するには先に削除してください"
  $CHECK_ONLY && exit 0 || exit 1
fi

$CHECK_ONLY && { echo ""; echo "→ '--check' モード: 変更は行いませんでした"; exit 0; }

# --- 実行フェーズ ---

# BSD sed 対応: ] だけ第2パスで別途エスケープ
_escape_sed_pattern() {
  printf '%s' "$1" | sed 's/[.^$*\\[]/\\&/g' | sed 's/]/\\]/g'
}

D=$'\x01'  # パスに含まれない非印字文字をデリミタに使用

SRC_PATH_ESC=$(_escape_sed_pattern "$SRC_PATH")
SRC_KEY_ESC=$(_escape_sed_pattern "$SRC_KEY")

echo ""
echo "履歴ディレクトリを移動中..."
mv "$SRC_DIR" "$DST_DIR"

echo "ファイル内のパスを更新中..."
updated=0
skipped=0

while IFS= read -r f; do
  if ! file "$f" | grep -qE 'text|JSON|ASCII'; then
    skipped=$((skipped + 1))
    continue
  fi

  # sed -i '' は mtime を更新するので退避・復元する
  mtime=$(stat -f "%m" "$f")

  # ファイルシステムパス形式（末尾アンカー: / か "）
  sed -i '' "s${D}${SRC_PATH_ESC}/${D}${DST_PATH}/${D}g" "$f"
  sed -i '' "s${D}${SRC_PATH_ESC}\"${D}${DST_PATH}\"${D}g" "$f"
  # Claude ディレクトリ名形式（/ と . を - に変換済み）
  sed -i '' "s${D}${SRC_KEY_ESC}/${D}${DST_KEY}/${D}g" "$f"
  sed -i '' "s${D}${SRC_KEY_ESC}\"${D}${DST_KEY}\"${D}g" "$f"

  # mtime を復元（/resume の時系列ソートを維持するため）
  touch -t "$(date -r "$mtime" "+%Y%m%d%H%M.%S")" "$f"

  updated=$((updated + 1))
done < <(find "$DST_DIR" -type f)

echo ""
echo "完了: $updated ファイル更新、$skipped ファイルスキップ（バイナリ）"
echo "OK: $SRC_PATH -> $DST_PATH"
