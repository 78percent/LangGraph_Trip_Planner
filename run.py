"""Project-root backend entry: run with Python or the IDE's Run button."""

from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    executable = root / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not executable.exists():
        print('Missing project virtual environment: .venv')
        print('See README.md for installation instructions.')
        return 1
    print('Starting backend with the project virtual environment...', flush=True)
    print('API docs: http://127.0.0.1:8000/docs', flush=True)
    print('Keep this terminal open. Start the frontend in a second terminal.', flush=True)
    try:
        return subprocess.call([str(executable), '-u', str(root / 'backend/run.py')], cwd=root)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
