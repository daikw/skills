#!/usr/bin/env bash
set -euo pipefail

# QCAD headless drawing wrapper
# Usage: qcad-draw.sh <snippet.js> [-o output.dxf] [--png]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_JS="${SCRIPT_DIR}/lib.js"

# --- Locate QCAD binary ---
QCAD_BIN=""
for candidate in \
    /Applications/QCAD.app/Contents/Resources/qcad \
    /usr/local/bin/qcad \
    "$(command -v qcad 2>/dev/null || true)"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        QCAD_BIN="$candidate"
        break
    fi
done

if [[ -z "$QCAD_BIN" ]]; then
    echo "ERROR: QCAD binary not found" >&2
    exit 1
fi

# --- Parse arguments ---
SNIPPET=""
OUTPUT=""
DO_PNG=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output) OUTPUT="$2"; shift 2 ;;
        --png) DO_PNG=true; shift ;;
        -h|--help)
            echo "Usage: qcad-draw.sh <snippet.js> [-o output.dxf] [--png]"
            echo ""
            echo "  <snippet.js>   JS file using Drawing API from lib.js"
            echo "  -o, --output   Output DXF path (default: <snippet>-output.dxf)"
            echo "  --png          Also generate PNG via ezdxf (requires uv + ezdxf)"
            exit 0
            ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *)
            if [[ -z "$SNIPPET" ]]; then
                SNIPPET="$1"
            else
                echo "ERROR: unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$SNIPPET" ]]; then
    echo "ERROR: no snippet file specified" >&2
    exit 1
fi

# Resolve absolute path
if [[ "$SNIPPET" != /* ]]; then
    SNIPPET="$(cd "$(dirname "$SNIPPET")" && pwd)/$(basename "$SNIPPET")"
fi

if [[ ! -f "$SNIPPET" ]]; then
    echo "ERROR: snippet file not found: $SNIPPET" >&2
    exit 1
fi

# Default output
if [[ -z "$OUTPUT" ]]; then
    OUTPUT="$(dirname "$SNIPPET")/$(basename "$SNIPPET" .js)-output.dxf"
fi
if [[ "$OUTPUT" != /* ]]; then
    OUTPUT="$(pwd)/$OUTPUT"
fi

# --- Build combined script ---
TMPSCRIPT="$(mktemp /tmp/qcad-draw-XXXXXX.js)"
trap 'rm -f "$TMPSCRIPT"' EXIT

cat > "$TMPSCRIPT" <<WRAPPER_EOF
include("scripts/library.js");
include("${LIB_JS}");

var _qcadDrawOutput = "${OUTPUT}";

function _qcadDrawMain() {
WRAPPER_EOF

cat "$SNIPPET" >> "$TMPSCRIPT"

cat >> "$TMPSCRIPT" <<'WRAPPER_TAIL'
}

if (typeof(including) == 'undefined' || including === false) {
    try {
        _qcadDrawMain();
    } catch (e) {
        print("QCAD_ERROR: " + e);
        // QCAD always exits 0, so we mark failure in output
        var f = new QFile(_qcadDrawOutput + ".error");
        f.open(QIODevice.WriteOnly);
        f.write(new QByteArray("" + e));
        f.close();
    }
}
WRAPPER_TAIL

# --- Execute QCAD ---
QCAD_OUTPUT=$("$QCAD_BIN" -no-gui -no-dock-icon -allow-multiple-instances \
    -autostart "$TMPSCRIPT" 2>&1) || true

echo "$QCAD_OUTPUT"

# --- Validate result ---
FAILED=false

# Check for error marker file
if [[ -f "${OUTPUT}.error" ]]; then
    echo "ERROR: QCAD script threw exception: $(cat "${OUTPUT}.error")" >&2
    rm -f "${OUTPUT}.error"
    FAILED=true
fi

# Check for QCAD_ERROR in output
if echo "$QCAD_OUTPUT" | grep -q "QCAD_ERROR"; then
    FAILED=true
fi

# Check DXF exists and is non-empty
if [[ ! -s "$OUTPUT" ]]; then
    echo "ERROR: DXF output missing or empty: $OUTPUT" >&2
    FAILED=true
fi

if $FAILED; then
    exit 1
fi

echo "DXF: $OUTPUT ($(wc -c < "$OUTPUT") bytes)"

# --- Optional PNG conversion ---
if $DO_PNG; then
    PNG_OUTPUT="${OUTPUT%.dxf}.png"
    if command -v uv >/dev/null 2>&1; then
        uv run --with 'ezdxf[draw]==1.4.2' python -c "
import ezdxf
from ezdxf.addons.drawing import matplotlib as mpl_draw
doc = ezdxf.readfile('${OUTPUT}')
msp = doc.modelspace()
mpl_draw.qsave(msp, '${PNG_OUTPUT}', dpi=150)
print('PNG: ${PNG_OUTPUT}')
" 2>&1 | tail -1
    else
        echo "WARN: uv not found, skipping PNG conversion" >&2
    fi
fi
