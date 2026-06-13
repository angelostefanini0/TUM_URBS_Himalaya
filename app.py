"""Backward-compatible launcher. Prefer `python run.py`."""

from run import app


if __name__ == '__main__':
    app.run()
