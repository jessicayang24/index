# 在 VS Code 运行网址管理程序

现在完整项目位于 `/Users/yangxiaoba/Workspace/05_website`。数据、Git 仓库和本地登录配置均独立存放于此，不依赖旧 SUM 目录。不要只复制 navigation.py，它需要同目录的 scripts、data 和仓库。

1. VS Code 打开「导航管理.code-workspace」。
2. 安装 Microsoft Python 扩展（含 Python Debugger）。
3. 填写并保存「网站操作.txt」，格式见「一键使用说明.md」。
4. 打开「一键处理.py」，点击 Run Python File in Terminal；也可在运行和调试中选择「一键处理操作清单」后按 F5。查询显示结果，修改自动提交推送。

可选的旧菜单仍保留在 navigation.py 中，仅在需要逐项交互时使用。以下描述适用于旧菜单：新增可只填网址；修改时回车保留原值，说明输入 - 清空；删除输入 DELETE 确认。

编辑后自动保存到本地并备份到 .local-publish/。只有选择 5 才会上传；退出不会丢失已保存的改动。推送仍包含本项目的程序维护文件。推送成功后需等待 GitHub Actions 构建及部署完成。

日常只使用「网站操作.txt」和「一键处理.py」。重复的 .command 推送入口已移除，旧「新增网址.txt」不会被新入口导入。

终端命令：

```bash
cd /Users/yangxiaoba/Workspace/05_website
python3 一键处理.py
# 只检查，不联网或推送
python3 navigation.py --check
# 导入新增网址.txt，并直接提交推送
python3 navigation.py --publish
```

第一次运行会自动创建虚拟环境并安装依赖。GitHub 登录沿用迁移过来的本地配置；若会话失效，在此目录运行「重新登录GitHub.command」。不要把 .local-publish/ 或令牌提交 Git，也不要把令牌交给 Copilot。

以后请在此目录维护同一份数据，旧目录并未自动删除。移动整个项目后应重新运行登录脚本，更新凭据辅助命令中的路径。
