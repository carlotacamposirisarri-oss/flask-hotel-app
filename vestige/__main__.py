"""Run locally:  python -m vestige   (from the repository root)."""
import os

from dotenv import load_dotenv

load_dotenv()

from . import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    # No authentication yet: bind to localhost unless you put it behind auth.
    app.run(host=os.environ.get("VESTIGE_HOST", "127.0.0.1"), port=int(os.environ.get("VESTIGE_PORT", 5050)),
            debug=os.environ.get("FLASK_DEBUG") == "1")
