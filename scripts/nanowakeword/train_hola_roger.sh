#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-nanowakeword"
ARCH="lstm"
PILOT="false"
REGENERATE_CONFIGS="false"

usage() {
  cat <<'EOF'
Usage: scripts/nanowakeword/train_hola_roger.sh [lstm|gru|tcn|all] [--pilot] [--generate-configs]

Defaults:
  architecture: lstm
  mode: full training config

Examples:
  scripts/nanowakeword/train_hola_roger.sh lstm --pilot
  scripts/nanowakeword/train_hola_roger.sh all
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    lstm|gru|tcn|all)
      ARCH="$1"
      shift
      ;;
    --pilot)
      PILOT="true"
      REGENERATE_CONFIGS="true"
      shift
      ;;
    --generate-configs)
      REGENERATE_CONFIGS="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

if [[ ! -x "$VENV_DIR/bin/python" || ! -x "$VENV_DIR/bin/nanowakeword" ]]; then
  echo "ERROR: $VENV_DIR is not ready. Run scripts/nanowakeword/setup_env.sh first." >&2
  exit 1
fi

CONFIG_DIR="configs/nanowakeword"
if [[ "$PILOT" == "true" ]]; then
  CONFIG_DIR="configs/nanowakeword/pilot"
fi

if [[ "$REGENERATE_CONFIGS" == "true" ]]; then
  if [[ "$PILOT" == "true" ]]; then
    "$VENV_DIR/bin/python" scripts/nanowakeword/generate_configs.py --output-dir "$CONFIG_DIR" --pilot
  else
    "$VENV_DIR/bin/python" scripts/nanowakeword/generate_configs.py --output-dir "$CONFIG_DIR"
  fi
fi

run_arch() {
  local arch="$1"
  local config="$CONFIG_DIR/hola_roger_${arch}.yaml"
  if [[ ! -f "$config" ]]; then
    echo "Config $config not found; generating configs first."
    if [[ "$PILOT" == "true" ]]; then
      "$VENV_DIR/bin/python" scripts/nanowakeword/generate_configs.py --output-dir "$CONFIG_DIR" --pilot
    else
      "$VENV_DIR/bin/python" scripts/nanowakeword/generate_configs.py --output-dir "$CONFIG_DIR"
    fi
  fi

  echo "Starting NanoWakeWord training for $arch using $config"
  "$VENV_DIR/bin/nanowakeword" -c "$config"
}

case "$ARCH" in
  all)
    run_arch lstm
    run_arch gru
    run_arch tcn
    ;;
  lstm|gru|tcn)
    run_arch "$ARCH"
    ;;
esac
