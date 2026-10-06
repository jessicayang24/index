"""Apply a text plan atomically, then publish without importing the old inbox."""
import copy
from datetime import datetime
import hashlib
import json

import yaml
import manage
import publish
import sites

TEMPLATE = """# 网站操作清单：写好后保存，运行「一键处理.py」或双击「一键处理.command」。
# 一行一条；| 两边有没有空格都可以；以 # 开头的示例不会执行。
# 新增：新增 | 网址 | 名称（可省略） | 分类（可省略） | 说明（可省略）
# 删除：删除 | 已保存的完整网址
# 修改：修改 | 已保存的完整旧网址 | 新网址（留空不变） | 名称（留空不变） | 分类（留空不变） | 说明（留空不变，- 清空）
# 查询：查询 | 关键词（留空查询全部）。查询结果会显示完整网址，可复制用于删除。
# 查询 | deeplearning
# 新增 | https://example.org/ | 示例网站 | 常用推荐 | 示例说明
# 删除 | https://example.org/
# 修改 | https://example.org/ | https://example.net/ | 新名称
# 成功后自动备份并清空；失败后保留，直接再运行即可。旧「新增网址.txt」不会被此入口导入。

"""


def digest(value):
    return hashlib.sha256(value).hexdigest()


def plan(data, text):
    result = copy.deepcopy(data)
    sites.validate(result)
    logs, mutations = [], False
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = [part.strip() for part in line.split("|")]
        action = fields[0]
        try:
            if action == "查询":
                if len(fields) != 2:
                    raise ValueError("格式：查询 | 关键词")
                found = manage.matches(result, fields[1])
                logs.extend(f"查询：[{c}] {s['name']} | {s['url']}" for _, c, s in found)
                if not found:
                    logs.append("查询：没有匹配网址")
                continue
            if action == "新增":
                if not 2 <= len(fields) <= 5:
                    raise ValueError("格式：新增 | 网址 | 名称 | 分类 | 说明")
                entries = publish.parse_inbox("|".join(fields[1:]))
                result, count = publish.merge(result, entries)
                logs.append(f"新增 {count} 条：{fields[1]}")
            elif action in ("删除", "修改"):
                if (action == "删除" and len(fields) != 2) or (action == "修改" and not 3 <= len(fields) <= 6):
                    raise ValueError("删除用两列；修改用：修改 | 旧网址 | 新网址 | 名称 | 分类 | 说明")
                key = sites.url_key(fields[1])
                found = [(pos, cat, s) for pos, cat, s in manage.matches(result, "") if sites.url_key(s["url"]) == key]
                if len(found) != 1:
                    raise ValueError(f"完整网址匹配到 {len(found)} 条记录，请先用 查询 核对；重复记录请在菜单中处理")
                pos, cat, site = found[0]
                if action == "删除":
                    result = manage.change(result, pos)
                else:
                    fields += [""] * (6 - len(fields))
                    replacement = dict(site)
                    for field, value in (("url", fields[2]), ("name", fields[3]), ("description", fields[5])):
                        if value:
                            replacement[field] = "" if field == "description" and value == "-" else value
                    result = manage.change(result, pos, fields[4] or cat, replacement)
                logs.append(f"{action}：{site['name']} | {site['url']}")
            else:
                raise ValueError("首列请填写 新增、查询、修改 或 删除")
            mutations = True
        except ValueError as error:
            raise ValueError(f"网站操作.txt 第 {number} 行：{error}") from error
    return result, logs, mutations


def main():
    inbox = sites.ROOT / "网站操作.txt"
    if not inbox.exists():
        inbox.write_text(TEMPLATE, encoding="utf-8")
        print(f"已生成 {inbox}，填写并保存后重新运行。")
        return
    text = inbox.read_text(encoding="utf-8-sig")
    state = sites.ROOT / ".local-publish"
    state.mkdir(exist_ok=True)
    lock = state / "running.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError("另一个编辑或推送程序正在运行")
    receipt = state / "batch-pending.json"
    try:
        before = sites.DATA.read_bytes()
        if receipt.exists():
            pending = json.loads(receipt.read_text())
            if pending["input"] != digest(text.encode()):
                raise ValueError("上批操作尚未推送成功，请恢复上次操作清单后重试；备份在 .local-publish 中")
            if digest(before) == pending["before"]:
                after = pending["after"].encode()
            elif digest(before) == digest(pending["after"].encode()):
                after = before
            else:
                raise ValueError("上批失败后网址数据又有改动，请先核对；未覆盖现有内容")
            print("继续推送上次保存的批量操作，不重复删除或修改。")
        else:
            data = yaml.load(before.decode(), Loader=sites.UniqueLoader)
            result, logs, mutations = plan(data, text)
            for message in logs:
                print(message)
            if not mutations:
                print("仅查询或清单为空，没有修改或推送。")
                return
            after = yaml.safe_dump(result, allow_unicode=True, sort_keys=False).encode()
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            (state / f"{stamp}-batch-sites.yml").write_bytes(before)
            (state / f"{stamp}-batch-操作.txt").write_text(text, encoding="utf-8")
            pending = {"input": digest(text.encode()), "before": digest(before), "after": after.decode()}
            receipt.write_text(json.dumps(pending, ensure_ascii=False), encoding="utf-8")
        if after != before:
            temporary = sites.DATA.with_suffix(".tmp")
            temporary.write_bytes(after)
            temporary.replace(sites.DATA)
        publish.publish(include_inbox=False)
        if inbox.read_text(encoding="utf-8-sig") == text:
            inbox.write_text(TEMPLATE, encoding="utf-8")
        else:
            print("操作清单运行期间有新编辑，已保留。")
        receipt.unlink()
        print("全部完成，原始数据与操作清单已备份在 .local-publish。")
    finally:
        lock.rmdir()
