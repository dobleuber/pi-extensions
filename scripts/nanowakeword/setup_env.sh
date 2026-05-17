#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-nanowakeword"
PYTHON_VERSION="3.12"

cd "$ROOT_DIR"

find_python() {
  if command -v uv >/dev/null 2>&1; then
    if uv python find "$PYTHON_VERSION" >/dev/null 2>&1; then
      uv python find "$PYTHON_VERSION"
      return 0
    fi
    echo "Python $PYTHON_VERSION not found via uv; installing it with uv..." >&2
    uv python install "$PYTHON_VERSION"
    uv python find "$PYTHON_VERSION"
    return 0
  fi

  if command -v python3.12 >/dev/null 2>&1; then
    command -v python3.12
    return 0
  fi

  echo "ERROR: Python 3.12 is required. Install uv or python3.12 first." >&2
  return 1
}

PYTHON_BIN="$(find_python)"
echo "Using Python: $PYTHON_BIN"

if command -v uv >/dev/null 2>&1; then
  uv venv --python "$PYTHON_BIN" "$VENV_DIR"
  VENV_PYTHON="$VENV_DIR/bin/python"
  uv pip install --python "$VENV_PYTHON" --upgrade pip wheel setuptools
  uv pip install --python "$VENV_PYTHON" \
    "nanowakeword[train] @ git+https://github.com/arcosoph/nanowakeword.git" \
    piper-tts
else
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  VENV_PYTHON="$VENV_DIR/bin/python"
  "$VENV_PYTHON" -m pip install --upgrade pip wheel setuptools
  "$VENV_PYTHON" -m pip install \
    "nanowakeword[train] @ git+https://github.com/arcosoph/nanowakeword.git" \
    piper-tts
fi

"$VENV_DIR/bin/nanowakeword" --help >/dev/null
"$VENV_PYTHON" - <<'PY'
import importlib.metadata as md
import torch
import nanowakeword
import piper.voice

print("nanowakeword", md.version("nanowakeword"))
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("cuda_device", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
PY

cat <<EOF

NanoWakeWord training environment is ready.
Activate it with:
  source .venv-nanowakeword/bin/activate

Next:
  .venv-nanowakeword/bin/python scripts/nanowakeword/download_assets.py
  scripts/nanowakeword/train_hola_roger.sh lstm --pilot
EOF
