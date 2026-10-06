#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
finish() {
  code=$?
  if [ "$code" -ne 0 ]; then
    printf '\n登录配置未完成，请查看上方提示。网址清单没有改动。\n'
  fi
  if [ -t 0 ]; then
    read -r -p '按回车关闭窗口...' answer || true
  fi
}
trap finish EXIT

# Use browser authorization instead of an environment-provided old token.
unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
gh_bin="$(command -v gh || true)"
if [ -z "$gh_bin" ]; then
  printf '请先在 Terminal 执行：brew install gh\n'
  exit 1
fi
# Keep CLI settings in this repository's ignored, writable local directory.
export GH_CONFIG_DIR="$PWD/.local-publish/gh-config"
umask 077
mkdir -p "$GH_CONFIG_DIR"
# Check persistence before asking the user to authorize in the browser.
"$gh_bin" config set git_protocol https --host github.com
printf '请使用 jessicayang24 登录。按终端提示，在 GitHub 浏览器页面输入一次性验证码并授权。\n'
printf '不需要粘贴个人访问令牌，也不要把验证码发送给别人。\n'
"$gh_bin" auth login --hostname github.com --git-protocol https --web --scopes workflow
account="$("$gh_bin" api user --jq .login)"
if [ "$account" != 'jessicayang24' ]; then
  printf '当前账号为 %s，请重新运行并登录 jessicayang24。\n' "$account"
  exit 1
fi

# Override cached keychain credentials only for this repository.
printf -v credential_helper '!env -u GH_TOKEN -u GITHUB_TOKEN GH_CONFIG_DIR=%q %q auth git-credential' "$GH_CONFIG_DIR" "$gh_bin"
git config --local --replace-all credential.https://github.com.helper ''
git config --local --add credential.https://github.com.helper "$credential_helper"
git config --local credential.https://github.com.username jessicayang24
printf '\n浏览器登录已完成，此仓库已改用 GitHub CLI 获取凭据。\n'
printf '现在关闭此窗口，再双击「一键推送.command」。\n'
