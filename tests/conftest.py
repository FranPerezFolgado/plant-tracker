import sys
from pathlib import Path


def pytest_configure() -> None:
    """
    Tests import modules the same way Docker runs the app:
    `uvicorn main:app` with `PYTHONPATH=app`.
    """
    repo_root = Path(__file__).resolve().parents[1]
    app_dir = repo_root / "app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

