"""Local bookmark editing with backup, validation and explicit publishing."""
import argparse
import copy
from datetime import datetime
import subprocess

import yaml
import publish
import sites


def change(data, position, category_name=None, site=None):
    result = copy.deepcopy(data)
    sites.validate(result)
    if site is not None:
        if not category_name or not category_name.strip():
            raise ValueError("分类名称不能为空")
        key = sites.url_key(site.get("url"))
        for ci, category in enumerate(result["categories"]):
            for si, other in enumerate(category["sites"]):
                if (ci, si) != position and sites.url_key(other["url"]) == key:
                    unchanged = position is not None and key == sites.url_key(
                        data["categories"][position[0]]["sites"][position[1]]["url"])
                    if not unchanged:
                        raise ValueError(f"网址已存在：{category['name']}/{other['name']}")
    if position is not None:
        ci, si = position
        if site is not None and result["categories"][ci]["name"] == category_name:
            result["categories"][ci]["sites"][si] = site
            sites.validate(result)
            return result
        del result["categories"][ci]["sites"][si]
    if site is not None:
        category = next((c for c in result["categories"] if c["name"] == category_name), None)
        if category is None:
            category = {"name": category_name, "sites": []}
            result["categories"].append(category)
        category["sites"].append(site)
    sites.validate(result)
    return result


def save(data, previous):
    sites.validate(data)
    state = sites.ROOT / ".local-publish"
    state.mkdir(exist_ok=True)
    lock = state / "running.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError("另一个程序正在保存或推送，请稍后重试")
    try:
        if sites.DATA.read_bytes() != previous:
            raise ValueError("数据已被其他程序修改，请重新选择网址后编辑")
        backup = state / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + "-sites.yml")
        backup.write_bytes(previous)
        temporary = sites.DATA.with_suffix(".tmp")
        temporary.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        temporary.replace(sites.DATA)
    finally:
        lock.rmdir()
    print("已保存到本地并备份；选择 5 提交推送。")


def matches(data, query):
    return [((ci, si), c["name"], s)
            for ci, c in enumerate(data["categories"])
            for si, s in enumerate(c["sites"])
            if query.casefold() in " ".join((c["name"], s["name"], s["url"], s.get("description", ""))).casefold()]


def edit(choice):
    previous = sites.DATA.read_bytes()
    data = yaml.load(previous.decode("utf-8"), Loader=sites.UniqueLoader)
    sites.validate(data)
    if choice == "1":
        print("格式：网址 或 网址 | 名称 | 分类 | 说明")
        line = input("输入新网址，回车取消：").strip()
        entries = publish.parse_inbox(line)
        if not entries:
            return
        category, site = entries[0]
        updated = change(data, None, category, site)
    else:
        found = matches(data, input("搜索名称、分类或网址，回车列出全部：").strip())
        for number, (_, category, site) in enumerate(found, 1):
            print(f"{number}. [{category}] {site['name']}  {site['url']}")
        if not found:
            print("没有匹配网址")
            return
        answer = input("选择序号，回车取消：").strip()
        if not answer:
            return
        if not answer.isdigit() or not 1 <= int(answer) <= len(found):
            raise ValueError("序号不在列表中")
        position, category, site = found[int(answer) - 1]
        if choice == "4":
            if input(f"删除 {site['name']}？输入 DELETE 确认：").strip() != "DELETE":
                print("已取消")
                return
            updated = change(data, position)
        else:
            print("回车保留原值；说明输入 - 可清空。")
            replacement = dict(site)
            for field, label in (("name", "名称"), ("url", "网址"), ("description", "说明")):
                answer = input(f"{label} [{site.get(field, '')}]：").strip()
                if answer:
                    replacement[field] = "" if field == "description" and answer == "-" else answer
            category = input(f"分类 [{category}]：").strip() or category
            updated = change(data, position, category, replacement)
    if updated != data:
        save(updated, previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="直接提交推送，并导入新增网址.txt")
    parser.add_argument("--check", action="store_true", help="只检查数据，不推送")
    parser.add_argument("--batch", action="store_true", help="处理网站操作.txt 并自动推送")
    args = parser.parse_args()
    if args.batch:
        import batch
        batch.main()
        return 0
    if args.check:
        count, warnings = sites.validate(sites.read(sites.DATA))
        print(f"检查通过：{count} 条网址")
        for warning in warnings:
            print(warning)
        return 0
    if args.publish:
        publish.main()
        return 0
    print(f"网址管理器\n项目位置：{sites.ROOT}")
    while True:
        print("\n1 新增   2 查找/查看   3 修改   4 删除   5 提交并推送   0 退出")
        choice = input("请选择：").strip()
        try:
            if choice == "0":
                return 0
            if choice in ("1", "3", "4"):
                edit(choice)
            elif choice == "2":
                for _, category, site in matches(sites.read(sites.DATA), input("搜索关键词：").strip()):
                    print(f"[{category}] {site['name']}\n  {site['url']}\n  {site.get('description', '')}")
            elif choice == "5":
                print("将提交本项目维护文件和网址到 jessicayang24/index；同时导入新增网址.txt。")
                publish.main()
            else:
                print("请输入菜单中的数字")
        except (ValueError, OSError, yaml.YAMLError, subprocess.CalledProcessError) as error:
            print(f"未完成：{error}\n本地文件仍保留，请修复后重试。")
