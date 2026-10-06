#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
finish() {
  if [ -t 0 ]; then
    read -r -p '按回车关闭窗口...' answer || true
  fi
}
trap finish EXIT
if [ -x .venv/bin/python ]; then
  .venv/bin/python 一键处理.py
else
  python3 一键处理.py
fi
