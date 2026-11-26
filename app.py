import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename
from segmentation import run_pipeline
from models import db, User, Analysis

app = Flask(__name__)
app.secret_key = "change-this-later"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["CACHE_FOLDER"] = "cache"
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB limit
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
ALLOWED_EXTENSIONS = {"csv", "xlsx"}

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def to_json_safe(o):
    return o.item() if hasattr(o, "item") else str(o)


def display_name(stored_name):
    # removes the "<user id>_" prefix
    return stored_name.split("_", 1)[1] if "_" in stored_name else stored_name


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or "@" not in email:
            flash("Please enter a valid email.")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("That email is already registered. Please log in.")
            return redirect(url_for("login"))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("upload"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Wrong email or password.")
            return redirect(url_for("login"))
        login_user(user)
        return redirect(url_for("upload"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please choose a file.")
            return redirect(url_for("upload"))
        if not allowed_file(file.filename):
            flash("Only .csv or .xlsx files are allowed.")
            return redirect(url_for("upload"))

        # prefix with the user id so users never overwrite each other's files
        filename = f"{current_user.id}_{secure_filename(file.filename)}"
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.session.add(Analysis(user_id=current_user.id, filename=filename))
        db.session.commit()
        return redirect(url_for("results", filename=filename))

    return render_template("upload.html")


@app.route("/results/<filename>")
@login_required
def results(filename):
    filename = secure_filename(filename)
    # users can only open their own files
    if not filename.startswith(f"{current_user.id}_"):
        flash("You can only view your own analyses.")
        return redirect(url_for("history"))

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        flash("File not found. Please upload again.")
        return redirect(url_for("upload"))

    os.makedirs(app.config["CACHE_FOLDER"], exist_ok=True)
    cache_path = os.path.join(app.config["CACHE_FOLDER"], filename + ".json")

    if os.path.exists(cache_path) and os.path.getmtime(cache_path) >= os.path.getmtime(path):
        with open(cache_path) as f:
            result = json.load(f)
        from_cache = True
    else:
        try:
            result = run_pipeline(path)
        except Exception as e:
            flash(f"Could not analyse this file: {e}")
            return redirect(url_for("upload"))
        with open(cache_path, "w") as f:
            json.dump(result, f, default=to_json_safe)
        from_cache = False

    return render_template("results.html", filename=display_name(filename),
                           result=result, from_cache=from_cache)


@app.route("/history")
@login_required
def history():
    analyses = (Analysis.query.filter_by(user_id=current_user.id)
                .order_by(Analysis.created_at.desc()).all())
    return render_template("history.html", analyses=analyses,
                           display_name=display_name)


if __name__ == "__main__":
    app.run(debug=True)