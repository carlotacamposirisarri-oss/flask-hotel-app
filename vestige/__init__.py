"""Vestige Intelligence — clienteling, competitive mapping, relationship strategy
and growth platform for Vestige (vestigeloyalty.com)."""
import os
import secrets

from datetime import timedelta

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

from . import ai, auth, db
from .prompts import KINDS


def _secret_key(app):
    path = os.path.join(app.instance_path, "flask_secret")
    os.makedirs(app.instance_path, exist_ok=True)
    if not os.path.exists(path):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(secrets.token_hex(32))
    with open(path) as fh:
        return fh.read().strip()


def create_app(instance_path=None):
    app = Flask(__name__, instance_path=instance_path or os.environ.get(
        "VESTIGE_INSTANCE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")))
    app.config.update(SECRET_KEY=os.environ.get("VESTIGE_SECRET_KEY") or _secret_key(app),
                      MAX_CONTENT_LENGTH=25 * 1024 * 1024,
                      SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax",
                      PERMANENT_SESSION_LIFETIME=timedelta(days=14))
    if os.environ.get("RENDER") or os.environ.get("VESTIGE_BEHIND_PROXY"):
        app.config["SESSION_COOKIE_SECURE"] = True
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.init_db()
        if os.environ.get("VESTIGE_DEMO_SEED") == "1":
            from .seed import seed
            seed()  # no-op once any maison exists

    from .views import bp
    app.register_blueprint(bp)
    app.register_blueprint(auth.bp)
    app.before_request(auth.guard)

    @app.route("/healthz")
    def healthz():
        return "ok"

    @app.context_processor
    def globals_():
        brand_list = db.query("SELECT id, name, sector, accent_color FROM brands ORDER BY name")
        return {"ai_status": ai.status(), "all_brands": brand_list, "KINDS": KINDS, "path": request.path,
                "auth_enabled": auth.auth_required()}

    @app.template_filter("money")
    def money(v):
        v = float(v or 0)
        if v >= 1_000_000:
            return f"€{v / 1_000_000:.1f}M"
        if v >= 1_000:
            return f"€{v / 1_000:.0f}k"
        return f"€{v:.0f}"

    @app.template_filter("label")
    def label(key):
        return str(key).replace("_", " ").capitalize()

    @app.template_filter("initials")
    def initials(name):
        return "".join(p[0] for p in str(name).split()[:2]).upper()

    return app
