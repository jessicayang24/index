"""Import a local URL inbox and publish only navigation project changes."""
import copy
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

import yaml
import sites

ROOT = sites.ROOT
INBOX = ROOT / "新增网址.txt"
EMPTY_INBOX = "# 一行一个网址；可选格式：网址 | 网站名称 | 分类 | 简短说明\n# 保存后双击「一键推送.command」。\n\n"
ALLOWED = {
    "config.yml", "data/sites.yml", "scripts/sites.py", "scripts/publish.py",
    "cmd/build/main.go", "go.mod", "go.sum", "requirements.txt", "README.md",
    "index.html", ".gitignore", ".github/workflows/generate.yml",
    "tests/test_sites.py", "tests/test_publish.py", "一键推送.command", "一键使用说明.md",
}


def git(*args, capture=True):
    result = subprocess.run(["git", *args], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None)
    if result.returncode:
        raise ValueError((result.stderr or "Git 操作失败，请查看终端提示。").strip())
    return result.stdout.strip() if capture else ""


def parse_inbox(text):
    entries = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split(" | ")]
        if len(fields) > 4:
            raise ValueError(f"第 {number} 行格式错误，请最多填写四列，用 空格|空格 分隔")
        url = fields[0]
        sites.url_key(url)
        fields += [""] * (4 - len(fields))
        entries.append((fields[2] or "待整理", {
            "name": fields[1] or urlsplit(url).hostname,
            "description": fields[3], "url": url,
        }))
    return entries


def merge(data, entries):
    data = copy.deepcopy(data)
    sites.validate(data)
    keys = {sites.url_key(s["url"]) for c in data["categories"] for s in c["sites"]}
    categories = {c["name"]: c for c in data["categories"]}
    added = 0
    for category_name, site in entries:
        key = sites.url_key(site["url"])
        if key in keys:
            print(f"已收录，跳过: {site['url']}")
            continue
        if category_name not in categories:
            category = {"name": category_name, "sites": []}
            categories[category_name] = category
            data["categories"].append(category)
        categories[category_name]["sites"].append(site)
        keys.add(key)
        added += 1
    sites.validate(data)
    return data, added


def changed_paths():
    # NUL separation keeps spaces and Chinese filenames intact.
    result = subprocess.check_output([
        "git", "ls-files", "-z", "--modified", "--deleted", "--others", "--exclude-standard"
    ], cwd=ROOT).decode()
    paths = set(filter(None, result.split("\0")))
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT).decode()
    return paths | set(filter(None, staged.split("\0")))


def publish():
    if git("branch", "--show-current") != "gh-pages":
        raise ValueError("请在 gh-pages 分支运行。脚本不会自动切换分支。")
    remote = git("remote", "get-url", "origin")
    if remote not in ("https://github.com/jessicayang24/index.git", "https://github.com/jessicayang24/index", "git@github.com:jessicayang24/index.git"):
        raise ValueError("origin 不是 jessicayang24/index，已停止推送。")
    for marker in ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD"):
        if (ROOT / git("rev-parse", "--git-path", marker)).exists():
            raise ValueError("存在未完成的合并或变基，请先处理 git status 中的问题。")
    extra = changed_paths() - ALLOWED
    if extra:
        raise ValueError("发现其他文件的改动，未自动提交：" + ", ".join(sorted(extra)))
    if not INBOX.exists():
        INBOX.write_text(EMPTY_INBOX, encoding="utf-8")
    original = INBOX.read_text(encoding="utf-8-sig")
    entries = parse_inbox(original)
    data, added = merge(sites.read(sites.DATA), entries)
    if not entries and not changed_paths():
        print("清单为空；如上次推送失败，将尝试同步已有提交。")
    print("正在连接 GitHub...", flush=True)
    git("fetch", "origin", "gh-pages", capture=False)
    if added:
        temporary = sites.DATA.with_suffix(".tmp")
        temporary.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        temporary.replace(sites.DATA)
    changed = changed_paths()
    if changed:
        # Require an actual configured identity; do not invent one.
        if not git("config", "--default", "", "--get", "user.name") or not git("config", "--default", "", "--get", "user.email"):
            raise ValueError("请先设置 git config user.name 和 git config user.email。")
        git("add", "--", *sorted(changed))
        if git("diff", "--cached", "--name-only"):
            git("commit", "-m", f"更新导航：新增 {added} 条网址及维护文件", capture=False)
    try:
        git("rebase", "origin/gh-pages", capture=False)
    except ValueError as error:
        raise ValueError("远端同步未完成。清单已保留；请用 git status 检查，必要时 git rebase --abort。") from error
    # Re-check after integrating remote edits, before pushing anything.
    git("diff", "--check")
    subprocess.run([sys.executable, "scripts/sites.py", "build-config"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT, check=True)
    git("push", "origin", "gh-pages", capture=False)
    if entries:
        backup = ROOT / ".local-publish" / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".txt")
        backup.write_text(original, encoding="utf-8")
        if INBOX.read_text(encoding="utf-8-sig") == original:
            INBOX.write_text(EMPTY_INBOX, encoding="utf-8")
        else:
            print("运行期间清单有新编辑，已保留当前内容。")
        print(f"本次清单备份：{backup}")
    print("推送成功。请等 GitHub Actions 构建、部署成功后查看网站。")
    print("https://github.com/jessicayang24/index/actions")
    print("https://jessicayang24.github.io/index/")


def main():
    state = ROOT / ".local-publish"
    state.mkdir(exist_ok=True)
    lock = state / "running.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError("发布脚本正在运行；若上次强制退出，请确认没有发布进程后删除 .local-publish/running.lock。")
    try:
        publish()
    finally:
        lock.rmdir()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        print(f"未完成：{error}\n待添加清单已保留，解决问题后可再次双击。", file=sys.stderr)
        sys.exit(1)
