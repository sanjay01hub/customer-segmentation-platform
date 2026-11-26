import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from segmentation import run_pipeline

app = Flask(__name__)
app.secret_key = "change-this-later"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB limit
ALLOWED_EXTENSIONS = {"csv", "xlsx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

    try:
        result = run_pipeline(path)
    except Exception as e:
        flash(f"Could not analyse this file: {e}")
        return redirect(url_for("upload"))

    return render_template("results.html", filename=filename, result=result)


if __name__ == "__main__":
    app.run(debug=True)