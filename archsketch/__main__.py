"""Allow running archsketch via python -m archsketch (works when archsketch.exe isn't on PATH)."""

from .main import app

if __name__ == "__main__":
    app()
