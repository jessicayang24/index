"""Manage navigation data and assemble the generator configuration."""
import argparse
import ipaddress
from pathlib import Path
import sys
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/sites.yml"


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"YAML 字段重复: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read(path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)


def url_key(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        raise ValueError(f"网址必须是无空格的字符串: {value!r}")
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise ValueError(f"请使用完整的 http/https 网址，且不要包含账户密码: {value}")
    _ = parts.port
    return (parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, parts.fragment)


def validate(data):
    if not isinstance(data, dict) or set(data) != {"categories"}:
        raise ValueError("data/sites.yml 顶层必须只有 categories")
    categories = data["categories"]
    if not isinstance(categories, list) or not categories:
        raise ValueError("categories 必须是非空列表")
    names, urls, warnings = set(), {}, []
    count = 0
    for category in categories:
        if not isinstance(category, dict) or set(category) != {"name", "sites"}:
            raise ValueError("每个分类必须包含 name 和 sites")
        name = category["name"]
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError(f"分类名为空或重复: {name}")
        names.add(name)
        if not isinstance(category["sites"], list):
            raise ValueError(f"{name}: sites 必须是列表")
        for site in category["sites"]:
            if not isinstance(site, dict) or set(site) - {"name", "url", "description", "icon"}:
                raise ValueError(f"{name}: 网站包含未知字段")
            if not isinstance(site.get("name"), str) or not site["name"].strip():
                raise ValueError(f"{name}: 网站缺少名称")
            if not isinstance(site.get("description", ""), str):
                raise ValueError(f"{site['name']}: description 必须是字符串，空值请写成 ''")
            key = url_key(site.get("url"))
            if site.get("icon"):
                url_key(site["icon"])
            label = f"{name}/{site['name']}"
            if key in urls:
                warnings.append(f"重复网址: {urls[key]} 与 {label}")
            urls[key] = label
            try:
                if ipaddress.ip_address(urlsplit(site["url"]).hostname).is_private:
                    warnings.append(f"局域网地址（外网通常无法访问）: {label}")
            except ValueError:
                pass
            count += 1
    return count, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("build-config")
    sub.add_parser("list")
    add = sub.add_parser("add")
    add.add_argument("--category", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--url", required=True)
    add.add_argument("--description", default="")
    add.add_argument("--new-category", action="store_true")
    args = parser.parse_args()
    data = read(DATA)
    count, warnings = validate(data)
    if args.command == "add":
        key = url_key(args.url)
        if any(url_key(s["url"]) == key for c in data["categories"] for s in c["sites"]):
            raise ValueError("网址已存在，请先查找并修改已有记录")
        category = next((c for c in data["categories"] if c["name"] == args.category), None)
        if category is None:
            if not args.new_category:
                raise ValueError("分类不存在，运行 list 查看分类；新建分类请加 --new-category")
            category = {"name": args.category, "sites": []}
            data["categories"].append(category)
        category["sites"].append({"name": args.name, "description": args.description, "url": args.url})
        count, warnings = validate(data)
        temporary = DATA.with_suffix(".tmp")
        temporary.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        temporary.replace(DATA)
    elif args.command == "build-config":
        config = read(ROOT / "config.yml")
        if not isinstance(config, dict) or "content" in config:
            raise ValueError("站点设置中不能包含 content，请在 data/sites.yml 管理网址")
        if config.get("template") != "webstack":
            raise ValueError("当前构建入口支持 webstack 主题")
        for field in ("title", "description", "footer"):
            if not isinstance(config.get(field), str):
                raise ValueError(f"站点设置 {field} 必须是字符串")
        for field in ("url", "favicon", "github"):
            url_key(config.get(field))
        config["content"] = data
        output = ROOT / ".build/config.yml"
        output.parent.mkdir(exist_ok=True)
        output.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    elif args.command == "list":
        for category in data["categories"]:
            print(f"{category['name']}: {len(category['sites'])} 个")
    print(f"检查通过: {len(data['categories'])} 个分类，{count} 条网址")
    for warning in warnings:
        print(f"提示: {warning}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, yaml.YAMLError) as error:
        print(f"错误: {error}", file=sys.stderr)
        sys.exit(1)
