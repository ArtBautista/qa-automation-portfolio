"""Content Portal: a small CMS-style Flask app used as the system under test (SUT).

Run locally:   python app/portal.py
Production-ish: waitress-serve --host=127.0.0.1 --port=5000 app.portal:app
Planted bugs:  set PORTAL_BUGS=1 before starting (used on Day 4).
"""
import os
import sqlite3
import time
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.serving import WSGIRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("PORTAL_DB", os.path.join(BASE_DIR, "portal.db"))
BUGS = os.environ.get("PORTAL_BUGS") == "1"
VERSION = "1.0.0"
TOKEN_MAX_AGE = 3600
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 300
VALID_STATUSES = ("draft", "published")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("PORTAL_SECRET", "dev-only-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="api-token")
failed_logins = {}  # username -> (failure_count, first_failure_timestamp)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('editor', 'viewer'))
);
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    author TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""
SEED_USERS = [
    ("editor", "Editor#2026", "editor"),
    ("viewer", "Viewer#2026", "viewer"),
]
SEED_ARTICLES = [
    ("Welcome to the Content Portal", "This portal publishes learning resources.", "published"),
    ("Exam Preparation Tips", "Plan your revision and practise past papers.", "published"),
    ("Draft: Upcoming Features", "Internal notes for the next release.", "draft"),
]


# ---------------------------------------------------------------- database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA)
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for username, password, role in SEED_USERS:
                db.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), role),
                )
            for title, body, status in SEED_ARTICLES:
                db.execute(
                    "INSERT INTO articles (title, body, status, author, created_at) "
                    "VALUES (?, ?, ?, 'editor', ?)",
                    (title, body, status, time.time()),
                )
            db.commit()


def find_article(article_id):
    return get_db().execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()


# ---------------------------------------------------------------- auth
def authenticate(username, password):
    """Return (user_row, error_message, http_status)."""
    count, first_failure = failed_logins.get(username, (0, 0.0))
    if count and time.time() - first_failure > LOCKOUT_SECONDS:
        failed_logins.pop(username, None)
        count = 0
    if count >= MAX_FAILED_LOGINS:
        return None, "Account temporarily locked. Try again later.", 429
    user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        failed_logins.pop(username, None)
        return user, None, 200
    failed_logins[username] = (count + 1, first_failure or time.time())
    return None, "Invalid username or password.", 401


def token_claims():
    """Return (claims, error_code). claims is None when the token is missing or bad."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, "missing_token"
    try:
        return serializer.loads(header[7:], max_age=TOKEN_MAX_AGE), None
    except SignatureExpired:
        return None, "token_expired"
    except BadSignature:
        return None, "invalid_token"


def require_token(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            claims, error = token_claims()
            if claims is None:
                return jsonify(error=error), 401
            if role and claims.get("role") != role:
                return jsonify(error="forbidden"), 403
            g.claims = claims
            return view(*args, **kwargs)

        return wrapped

    return decorator


def editor_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "editor":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def is_editor_request():
    claims, _ = token_claims()
    return bool(claims and claims.get("role") == "editor")


# ---------------------------------------------------------------- validation
def validate_article(data, partial=False):
    errors = {}
    if not partial or "title" in data:
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            errors["title"] = "Title is required."
        else:
            length = len(title.strip())
            too_long = length > 120 and not BUGS  # planted bug: max length not enforced
            if length < 3 or too_long:
                errors["title"] = "Title must be 3-120 characters."
    if not partial or "body" in data:
        body = data.get("body")
        if not isinstance(body, str) or not body.strip():
            errors["body"] = "Body is required."
        elif len(body) > 10000:
            errors["body"] = "Body must be 10000 characters or fewer."
    if not partial or "status" in data:
        if data.get("status", "draft") not in VALID_STATUSES:
            errors["status"] = "Status must be 'draft' or 'published'."
    return errors


# ---------------------------------------------------------------- security headers
@app.after_request
def add_security_headers(response):
    csp = "default-src 'self'; img-src 'self' data:; form-action 'self'"
    if not BUGS:  # planted bug: clickjacking protection missing
        response.headers["X-Frame-Options"] = "DENY"
        csp += "; frame-ancestors 'none'"
    response.headers["Content-Security-Policy"] = csp
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------- error handlers
def wants_json():
    return request.path.startswith("/api/")


@app.errorhandler(403)
def forbidden(_err):
    if wants_json():
        return jsonify(error="forbidden"), 403
    return render_template("error.html", code=403, message="You do not have access."), 403


@app.errorhandler(404)
def not_found(_err):
    if wants_json():
        return jsonify(error="not_found"), 404
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(405)
def method_not_allowed(_err):
    if wants_json():
        return jsonify(error="method_not_allowed"), 405
    return render_template("error.html", code=405, message="Method not allowed."), 405


@app.errorhandler(500)
def server_error(_err):
    if wants_json():
        return jsonify(error="internal_error"), 500
    return render_template("error.html", code=500, message="Something went wrong."), 500


# ---------------------------------------------------------------- web pages
@app.get("/")
def home():
    rows = get_db().execute(
        "SELECT id, title FROM articles WHERE status = 'published' ORDER BY id DESC"
    ).fetchall()
    return render_template("home.html", articles=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user, error, status_code = authenticate(username, password)
        if user:
            session.clear()
            session["user"] = user["username"]
            session["role"] = user["role"]
            flash("Signed in successfully.")
            return redirect(url_for("home"))
        return render_template("login.html", error=error), status_code
    return render_template("login.html", error=None)


@app.post("/logout")
def logout():
    session.clear()
    flash("Signed out.")
    return redirect(url_for("home"))


@app.get("/articles/<int:article_id>")
def view_article(article_id):
    article = find_article(article_id)
    if article is None:
        abort(404)
    if article["status"] != "published" and session.get("role") != "editor":
        abort(404)
    return render_template("article.html", article=article)


@app.route("/editor/articles/new", methods=["GET", "POST"])
@editor_required
def new_article():
    form = {"title": "", "body": "", "status": "draft"}
    errors = {}
    if request.method == "POST":
        form = {key: request.form.get(key, "") for key in ("title", "body", "status")}
        errors = validate_article(form)
        if not errors:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO articles (title, body, status, author, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (form["title"].strip(), form["body"], form["status"], session["user"],
                 time.time()),
            )
            db.commit()
            flash("Article created.")
            return redirect(url_for("view_article", article_id=cursor.lastrowid))
    status_code = 400 if errors else 200
    return render_template("editor.html", form=form, errors=errors), status_code


@app.get("/search")
def search():
    q = request.args.get("q", "").strip()
    results = []
    if q:
        results = get_db().execute(
            "SELECT id, title FROM articles WHERE status = 'published' AND title LIKE ? "
            "ORDER BY id DESC",
            (f"%{q}%",),
        ).fetchall()
    display_q = Markup(q) if BUGS else q  # planted bug: reflected XSS
    return render_template("search.html", q=q, display_q=display_q, results=results)


# ---------------------------------------------------------------- REST API
@app.get("/api/health")
def api_health():
    return jsonify(status="ok", version=VERSION)


@app.post("/api/auth/token")
def api_token():
    data = request.get_json(silent=True) or {}
    user, error, status_code = authenticate(
        str(data.get("username", "")), str(data.get("password", ""))
    )
    if user is None:
        return jsonify(error=error), status_code
    token = serializer.dumps({"user": user["username"], "role": user["role"]})
    return jsonify(token=token, expires_in=TOKEN_MAX_AGE)


@app.get("/api/articles")
def api_list_articles():
    status = request.args.get("status", "published")
    if status not in VALID_STATUSES + ("all",):
        return jsonify(error="invalid_status"), 400
    if status != "published" and not is_editor_request():
        return jsonify(error="editor_token_required"), 401
    try:
        limit = int(request.args.get("limit", "20"))
    except ValueError:
        return jsonify(error="invalid_limit"), 400
    if not 1 <= limit <= 100:
        return jsonify(error="invalid_limit"), 400

    clauses, params = [], []
    if status != "all":
        clauses.append("status = ?")
        params.append(status)
    q = request.args.get("q", "").strip()
    if q:
        clauses.append("title LIKE ?")
        params.append(f"%{q}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = get_db().execute(
        f"SELECT * FROM articles {where} ORDER BY id DESC LIMIT ?", (*params, limit)
    ).fetchall()
    items = [dict(row) for row in rows]
    return jsonify(items=items, count=len(items))


@app.get("/api/articles/<int:article_id>")
def api_get_article(article_id):
    article = find_article(article_id)
    if article is None or (article["status"] != "published" and not is_editor_request()):
        return jsonify(error="not_found"), 404
    return jsonify(dict(article))


@app.post("/api/articles")
@require_token(role="editor")
def api_create_article():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="invalid_json"), 400
    errors = validate_article(data)
    if errors:
        return jsonify(error="validation_failed", fields=errors), 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO articles (title, body, status, author, created_at) VALUES (?, ?, ?, ?, ?)",
        (data["title"].strip(), data["body"], data.get("status", "draft"),
         g.claims["user"], time.time()),
    )
    db.commit()
    article = dict(find_article(cursor.lastrowid))
    response = jsonify(article)
    response.status_code = 201
    response.headers["Location"] = url_for("api_get_article", article_id=article["id"])
    return response


@app.put("/api/articles/<int:article_id>")
@require_token(role="editor")
def api_update_article(article_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="invalid_json"), 400
    if find_article(article_id) is None:
        return jsonify(error="not_found"), 404
    errors = validate_article(data, partial=True)
    if errors:
        return jsonify(error="validation_failed", fields=errors), 400
    updates = {key: data[key] for key in ("title", "body", "status") if key in data}
    if "title" in updates:
        updates["title"] = updates["title"].strip()
    if updates:
        assignments = ", ".join(f"{column} = ?" for column in updates)
        db = get_db()
        db.execute(
            f"UPDATE articles SET {assignments} WHERE id = ?", (*updates.values(), article_id)
        )
        db.commit()
    return jsonify(dict(find_article(article_id)))


@app.delete("/api/articles/<int:article_id>")
@require_token(role="editor")
def api_delete_article(article_id):
    if find_article(article_id) is None:
        return jsonify(error="not_found"), 404
    db = get_db()
    db.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    db.commit()
    return "", 204


@app.get("/api/reports/popular")
def api_popular_report():
    time.sleep(0.6 if BUGS else 0.05)  # simulates a heavy query; planted perf bug when BUGS=1
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS total FROM articles GROUP BY status"
    ).fetchall()
    return jsonify(totals={row["status"]: row["total"] for row in rows})


class QuietRequestHandler(WSGIRequestHandler):
    """Dev server handler that hides the Werkzeug/Python versions in the Server header."""

    def version_string(self):
        return "content-portal"


init_db()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
        request_handler=QuietRequestHandler,
    )
