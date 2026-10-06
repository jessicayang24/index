"""在 VS Code 点击运行，处理网站操作.txt 并自动推送。"""
import sys
import navigation

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--batch"]
    try:
        sys.exit(navigation.main())
    except (Exception, KeyboardInterrupt) as error:
        print(f"未完成：{error}\n操作清单已保留。")
        sys.exit(1)
