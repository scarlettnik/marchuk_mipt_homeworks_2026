import sys
from collections.abc import Callable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_runner() -> Callable[[Path], int]:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from final_project.gigavibe_mipt_code.app import run_application

    return run_application


def main() -> int:
    project_root = Path(__file__).resolve().parent
    return get_runner()(project_root / 'config.yaml')


if __name__ == '__main__':
    raise SystemExit(main())
