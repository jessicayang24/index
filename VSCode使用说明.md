# 在 VS Code 运行网址管理程序

现在完整项目位于 `/Users/yangxiaoba/Workspace/05_website`。数据、Git 仓库和本地登录配置均独立存放于此，不依赖旧 SUM 目录。不要只复制 navigation.py，它需要同目录的 scripts、data 和仓库。

1. VS Code 打开「导航管理.code-workspace」。
2. 安装 Microsoft Python 扩展（含 Python Debugger）。
3. 打开 navigation.py，点击右上角 Run Python File in Terminal；也可在运行和调试中选择「网址管理菜单」，按 F5。
4. 根据终端菜单输入数字：1 新增、2 查看、3 修改、4 删除、5 提交并推送、0 退出。

新增时只填网址即可，自动归入“待整理”；也支持 `网址 | 网站名称 | 分类 | 说明`。修改时回车保留原值，说明输入 - 可清空。删除需要输入 DELETE 确认。

编辑后自动保存到本地并备份到 .local-publish/。只有选择 5 才会上传；退出不会丢失已保存的改动。推送仍包含本项目的程序维护文件。推送成功后需等待 GitHub Actions 构建及部署完成。

仍想用填写文件的方式：打开本目录「新增网址.txt」，保存后在运行和调试中选择「直接提交推送」。原有「一键推送.command」在此目录也可继续使用。

终端命令：

```bash
cd /Users/yangxiaoba/Workspace/05_website
python3 navigation.py
# 只检查，不联网或推送
python3 navigation.py --check
# 导入新增网址.txt，并直接提交推送
python3 navigation.py --publish
```

第一次运行会自动创建虚拟环境并安装依赖。GitHub 登录沿用迁移过来的本地配置；若会话失效，在此目录运行「重新登录GitHub.command」。不要把 .local-publish/ 或令牌提交 Git，也不要把令牌交给 Copilot。

以后请在此目录维护同一份数据，旧目录并未自动删除。移动整个项目后应重新运行登录脚本，更新凭据辅助命令中的路径。
