#!/usr/bin/env bash
# Render a PlantUML file to SVG and PNG via kroki.io public server.
# Usage: render.sh <input.puml> [--format svg|png|both]
# Default format: both. Output files are written next to the input.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <input.puml> [--format svg|png|both]" >&2
  exit 2
fi

input="$1"
format="both"

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --format)
      format="${2:-both}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$input" ]]; then
  echo "Input file not found: $input" >&2
  exit 1
fi

base="${input%.puml}"
if [[ "$base" == "$input" ]]; then
  base="${input%.*}"
fi

render_one() {
  local fmt="$1"
  local out="${base}.${fmt}"
  local http_status
  http_status=$(curl -sS -o "$out" -w '%{http_code}' \
    -X POST -H 'Content-Type: text/plain' \
    --data-binary "@${input}" \
    "https://kroki.io/plantuml/${fmt}")
  if [[ "$http_status" != "200" ]]; then
    echo "kroki returned HTTP ${http_status} for ${fmt}:" >&2
    cat "$out" >&2
    rm -f "$out"
    return 1
  fi
  echo "Rendered: $out"
}

case "$format" in
  svg) render_one svg ;;
  png) render_one png ;;
  both)
    render_one svg
    render_one png
    ;;
  *)
    echo "Invalid format: $format (use svg|png|both)" >&2
    exit 2
    ;;
esac
