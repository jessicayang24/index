# Jessica 的网址导航

## 一键添加（推荐）

打开同目录的「新增网址.txt」，一行写一个网址并保存，再双击「一键推送.command」。可选填名称、分类，格式见 [一键使用说明](一键使用说明.md)。脚本自动安装 Python 依赖、检查数据、提交、同步和推送；推送成功后备份并清空清单。首次使用仍需完成下文的 Pages 设置及 Git 认证。

[![Build](https://github.com/jessicayang24/index/actions/workflows/generate.yml/badge.svg)](https://github.com/jessicayang24/index/actions/workflows/generate.yml)

使用固定版本的 gena / WebStack 主题。日常网址在 `data/sites.yml`，站点设置在 `config.yml`；Git 保存和上传修改，Actions 自动生成网页。

Site address: https://jessicayang24.github.io/index/

## 架构

```text
config.yml                标题、主题、搜索引擎设置
data/sites.yml            网址与分类（日常编辑入口）
scripts/sites.py          添加、校验、合并配置
cmd/build/main.go         固定版本 gena 的构建入口
go.mod / go.sum           Go 依赖与校验
requirements.txt          Python 依赖
.github/workflows/        自动构建和部署
index.html                生成结果，不手工编辑
```

## 首次准备

已克隆仓库的人直接进入项目，无需再次 clone。

```bash
git clone https://github.com/jessicayang24/index.git
cd index
git switch gh-pages
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

首次迁移到此版本：GitHub 仓库 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**。源码仍在 gh-pages 分支，工作流部署生成的静态产物。在 Actions 手动运行一次工作流即可首次发布。

本次本地优化如尚未提交，先在本项目目录检查并上传整套改动（这一步仅需一次）：

```bash
git diff
git add config.yml data scripts cmd tests go.mod go.sum requirements.txt README.md index.html .gitignore .github/workflows/generate.yml
git commit -m '整理网址数据与自动发布架构'
git push origin gh-pages
```

完成这次迁移后，日常只需要提交 data/sites.yml。

## 每次添加网址

Git 命令本身不会修改网址数据，先用脚本添加，再提交和上传。

```bash
git switch gh-pages
git pull --ff-only origin gh-pages
source .venv/bin/activate
python scripts/sites.py add --category '数据工具' --name '国家统计局' --url 'https://www.stats.gov.cn/' --description '统计数据查询'
python scripts/sites.py check
git diff -- data/sites.yml
git add data/sites.yml
git commit -m '新增国家统计局网址'
git push origin gh-pages
```

pull 获取远端更新；diff 检查修改；add 选定文件；commit 在本机保存记录；push 上传。打开 GitHub Actions，确认 build 和 deploy 都成功后访问网站。

`python scripts/sites.py list` 查看分类；创建新分类在 add 命令末尾加 `--new-category`。网址务必用引号包住，特别是含有 & 或 ? 的网址。

也可以编辑 data/sites.yml，在相应 sites 列表下增加以下内容，缩进与相邻记录一致：

```yaml
  - name: 国家统计局
    description: 统计数据查询
    url: https://www.stats.gov.cn/
```

删除网址即删除整条记录，调整分类即移动整条记录。修改后仍运行 check 和上述 Git 命令。空说明写成 `description: ''`。

## 本地预览（可选）

日常增删网址不需要 Go，线上会自动安装。需要生成预览时先安装 Go 1.23.12 或兼容版本：

```bash
python scripts/sites.py build-config
go run -mod=readonly ./cmd/build
python -m http.server 8000
```

浏览器访问 http://localhost:8000/ ，按 Ctrl+C 停止。生成的 index.html 不需要提交，线上会重新构建。

## 原有数据与常见问题

全部原有分类与网址均保留，只将空说明规范为空字符串。重复链接提示但不阻断旧数据构建；add 命令拒绝再次加入重复网址。

- Gartner 出现在两个分类；“经济网站”和“政策网站”指向同一网址，建议人工决定合并或改址。
- “海关资讯”中混有软件、AI 论文和投资论坛，可逐步移入更匹配的分类。
- NAS 是局域网地址，外网通常无法访问。
- duckdyckgo 域名拼写、两个同名 Port Examiner 建议人工核对；未擅自替换地址。
- 校验只检查格式，不证明所有外部网站可用。

push 被拒绝且提示远端有新提交：先提交本地修改，再执行 `git pull --rebase origin gh-pages`，解决冲突后 push。若不确定，`git rebase --abort` 退出变基；不要强制推送。

HTTPS 认证失败：使用已配置的 GitHub 凭据、CLI 浏览器登录或 SSH，不能使用 GitHub 账户密码。不要把 token 放进数据文件或聊天。

build 成功但 deploy 失败：检查 Pages Source 是否为 GitHub Actions，以及 github-pages 环境是否允许 gh-pages 分支部署。

撤销已发布修改：用 `git log --oneline -5` 找到提交编号，执行 `git revert 提交编号`，再 `git push origin gh-pages`，保留历史。
