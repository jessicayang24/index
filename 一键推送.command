#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
finish() {
  code=$?
  if [ "$code" -ne 0 ]; then
    printf '\n未完成推送，待添加清单已保留。请查看上面的错误。\n'
  fi
  if [ -t 0 ]; then
    read -r -p '按回车关闭窗口...' answer || true
  fi
}
trap finish EXIT
printf '正在准备网址发布工具...\n'
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import yaml' 2>/dev/null; then
  .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python scripts/publish.py
