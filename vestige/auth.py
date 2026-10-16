"""Password gate for deployed instances.

Set VESTIGE_PASSWORD to require a login. On a hosted platform (RENDER or
VESTIGE_REQUIRE_AUTH set) the app refuses to serve anything until a password is
configured, so client data is never exposed by a missing env var.
"""
import hmac
import os
import time
from collections import defaultdict, deque

from flask import Blueprint, redirect, render_template, request, session, url_for

bp = Blueprint("auth", __name__)

MAX_ATTEMPTS = 5          # per IP ...
WINDOW_SECONDS = 15 * 60  # ... per 15 minutes
_attempts = defaultdict(deque)


def password():
    return os.environ.get("VESTIGE_PASSWORD", "")


def auth_required():
    return bool(password()) or bool(os.environ.get("RENDER") or os.environ.get("VESTIGE_REQUIRE_AUTH"))


def _client_ip():
    return request.remote_addr or "unknown"


def _throttled(ip):
    q = _attempts[ip]
    now = time.time()
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    return len(q) >= MAX_ATTEMPTS


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not password():
        return render_template("login.html", misconfigured=True), 503
    error = None
    if request.method == "POST":
        ip = _client_ip()
        if _throttled(ip):
            error = "Too many attempts. Try again in 15 minutes."
        elif hmac.compare_digest(request.form.get("password", "").encode(), password().encode()):
            _attempts.pop(ip, None)
            session.clear()
            session["auth"] = True
            session.permanent = True
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("v.dashboard"))
        else:
            _attempts[ip].append(time.time())
            error = "Incorrect password."
    return render_template("login.html", error=error), (401 if error else 200)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def guard():
    """before_request hook."""
    if not auth_required() or session.get("auth"):
        return None
    if request.endpoint in ("auth.login", "static", "healthz"):
        return None
    return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
