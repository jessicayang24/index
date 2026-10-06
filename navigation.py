"""Open in VS Code and choose Run Python File in Terminal."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    venv = ROOT / ".venv"
    python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if Path(sys.prefix).resolve() != venv.resolve():
        if not python.exists():
            print("首次运行：准备 Python 环境…", flush=True)
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        if subprocess.run([str(python), "-c", "import yaml"], capture_output=True).returncode:
            subprocess.run([str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)
        return subprocess.call([str(python), str(Path(__file__).resolve()), *sys.argv[1:]], cwd=ROOT)
    try:
        import yaml
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)
    sys.path.insert(0, str(ROOT / "scripts"))
    from manage import main as manage_main
    return manage_main()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\n已退出。已保存的本地修改仍保留。")
    except Exception as error:
        print(f"未完成：{error}", file=sys.stderr)
        sys.exit(1)
