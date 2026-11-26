import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from segmentation import run_pipeline

app = Flask(__name__)
app.secret_key = "change-this-later"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["CACHE_FOLDER"] = "cache"
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB limit
ALLOWED_EXTENSIONS = {"csv", "xlsx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def to_json_safe(o):
    # converts numpy numbers to normal Python numbers
    return o.item() if hasattr(o, "item") else str(o)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please choose a file.")
            return redirect(url_for("upload"))
        if not allowed_file(file.filename):
            flash("Only .csv or .xlsx files are allowed.")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return redirect(url_for("results", filename=filename))

    return render_template("upload.html")


@app.route("/results/<filename>")
def results(filename):
    filename = secure_filename(filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        flash("File not found. Please upload again.")
        return redirect(url_for("upload"))

    os.makedirs(app.config["CACHE_FOLDER"], exist_ok=True)
    cache_path = os.path.join(app.config["CACHE_FOLDER"], filename + ".json")

    # use saved results if they are newer than the uploaded file
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

    return render_template("results.html", filename=filename, result=result, from_cache=from_cache)


if __name__ == "__main__":
    app.run(debug=True)