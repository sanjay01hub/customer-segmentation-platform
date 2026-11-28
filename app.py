import os
import io
import csv
import json
from dotenv import load_dotenv
from flask import (Flask, render_template, request, redirect, url_for, flash,
                   send_file, Response, session)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename

load_dotenv()

from segmentation import load_data, clean_data, segment_customers, MAX_ROWS
from analytics import overview, product_movement, demand, audience, health
from insights import generate_insights, messages_for
from translate import translate_html, tr
from datareport import build_report
from stockreport import build_stock
from grow import advise, TYPES, GOALS
from models import db, User, Analysis

CACHE_VERSION = 3  # bump this when the result format changes

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["CACHE_FOLDER"] = "cache"
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB limit
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
ALLOWED_EXTENSIONS = {"csv", "tsv", "txt", "xlsx", "xlsm", "xls", "ods", "json", "jsonl", "pdf"}

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def current_lang():
    return "ta" if session.get("lang") == "ta" else "en"


@app.context_processor
def inject_language():
    lang = current_lang()
    return {"lang": lang, "_": lambda text: tr(text, lang)}


@app.after_request
def translate_response(response):
    """Swap English text for Tamil when the visitor chose Tamil."""
    if current_lang() == "ta" and response.mimetype == "text/html" and not response.direct_passthrough:
        response.set_data(translate_html(response.get_data(as_text=True)))
    return response


@app.route("/lang/<code>")
def set_lang(code):
    if code in ("en", "ta"):
        session["lang"] = code
    back = request.referrer or ""
    return redirect(back if back.startswith(request.host_url) else url_for("home"))


def looks_like_sales(path):
    """True only for a real sales file: customer, quantity, price and date columns are all present."""
    import re
    import pandas as pd
    if path.lower().rsplit(".", 1)[-1] not in ("csv", "xlsx"):
        return False          # the sales analysis only reads CSV / XLSX; others get the general report
    try:
        if path.lower().endswith(".xlsx"):
            head = pd.read_excel(path, nrows=50)
        else:
            head = pd.read_csv(path, nrows=50, encoding_errors="replace")
        keys = [re.sub(r"[^a-z0-9]", "", str(c).lower()) for c in head.columns]

        def has(words):
            return any(any(w in k for w in words) for k in keys)
        if not (has(("customer", "cust", "client")) and has(("quantity", "qty", "units"))
                and has(("price", "rate", "amount", "revenue")) and has(("date",))):
            return False
        from segmentation import standardise_columns
        standardise_columns(head)
        return True
    except Exception:
        return False


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def to_json_safe(o):
    return o.item() if hasattr(o, "item") else str(o)


def display_name(stored_name):
    return stored_name.split("_", 1)[1] if "_" in stored_name else stored_name


def cache_path(filename):
    return os.path.join(app.config["CACHE_FOLDER"], filename + ".json")


def customers_csv_path(filename):
    return os.path.join(app.config["CACHE_FOLDER"], filename + ".customers.csv")


def analyse(path, filename):
    """Run every analysis once and return one dict."""
    df, truncated = load_data(path)
    df = clean_data(df)
    result = {"version": CACHE_VERSION, "rows": len(df), "truncated": truncated,
              "max_rows": MAX_ROWS, "overview": overview(df)}
    seg, per_customer = segment_customers(df)
    result["segmentation"] = seg
    if seg:
        result["insights"] = generate_insights(seg["segments"])
        per_customer.to_csv(customers_csv_path(filename), index=False)
    result["products"] = product_movement(df)
    result["demand"] = demand(df)
    result["audience"] = audience(df)
    return result


def get_result(filename):
    """Load a user's analysis from cache, or build it. Returns (result, redirect_response)."""
    filename = secure_filename(filename)
    if not filename.startswith(f"{current_user.id}_"):
        flash("You can only view your own analyses.")
        return None, redirect(url_for("history"))
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        flash("File not found. Please upload again.")
        return None, redirect(url_for("upload"))

    os.makedirs(app.config["CACHE_FOLDER"], exist_ok=True)
    cp = cache_path(filename)
    if os.path.exists(cp) and os.path.getmtime(cp) >= os.path.getmtime(path):
        with open(cp) as f:
            result = json.load(f)
        if result.get("version") == CACHE_VERSION:
            return result, None
    try:
        result = analyse(path, filename)
    except Exception:
        flash("This is not a typical sales file, so here is a general report instead.")
        return None, redirect(url_for("report_view", filename=filename))
    with open(cp, "w") as f:
        json.dump(result, f, default=to_json_safe)
    return result, None


def page(template, filename):
    result, redirect_response = get_result(filename)
    if redirect_response:
        return redirect_response
    filename = secure_filename(filename)
    lang = current_lang()
    try:
        seg = result.get("segmentation")
        return render_template(template, filename=display_name(filename),
                               stored_name=filename, r=result,
                               health=health(result, lang),
                               messages=messages_for(seg["segments"], lang) if seg else [])
    except Exception:
        flash("This is not a typical sales file, so here is a general report instead.")
        return redirect(url_for("report_view", filename=filename))


# The four analysis pages
@app.route("/results/<filename>")
@login_required
def results(filename):
    return page("results.html", filename)


@app.route("/products/<filename>")
@login_required
def products(filename):
    return page("products.html", filename)


@app.route("/demand/<filename>")
@login_required
def demand_page(filename):
    return page("demand.html", filename)


@app.route("/audience/<filename>")
@login_required
def audience_page(filename):
    return page("audience.html", filename)


@app.route("/download/<filename>/<kind>")
@login_required
def download(filename, kind):
    result, redirect_response = get_result(filename)
    if redirect_response:
        return redirect_response
    filename = secure_filename(filename)
    base = display_name(filename).rsplit(".", 1)[0]

    if kind == "customers":
        p = customers_csv_path(filename)
        if not os.path.exists(p):
            flash("No customer segments for this file.")
            return redirect(url_for("results", filename=filename))
        return send_file(p, as_attachment=True, download_name=f"{base}_customer_segments.csv")

    buf = io.StringIO()
    w = csv.writer(buf)
    if kind == "slow" and result.get("products"):
        w.writerow(["Product", "Units sold", "Orders", "Days since last sale", "Why", "Idea"])
        for x in result["products"]["slow"]:
            w.writerow([x["name"], x["units"], x["orders"], x["days_since"], x["why"], x["idea"]])
    elif kind == "fast" and result.get("products"):
        w.writerow(["Product", "Units sold", "Revenue", "Units per month"])
        for x in result["products"]["fast"]:
            w.writerow([x["name"], x["units"], x["revenue"], x["per_month"]])
    else:
        flash("That download is not available for this file.")
        return redirect(url_for("results", filename=filename))
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={base}_{kind}.csv"})


@app.route("/history")
@login_required
def history():
    analyses = (Analysis.query.filter_by(user_id=current_user.id)
                .order_by(Analysis.created_at.desc()).all())
    return render_template("history.html", analyses=analyses, display_name=display_name)


# ------------------------------------------------------------------ four options
def save_upload():
    """Save the uploaded file for the current user. Returns (stored_name, error_redirect_endpoint)."""
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Please choose a file.")
        return None
    if not allowed_file(file.filename):
        flash("This file type is not supported. Use CSV, Excel, TSV, TXT, JSON, ODS or a PDF with a table.")
        return None
    filename = f"{current_user.id}_{secure_filename(file.filename)}"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return filename


def own_file(filename):
    """Return the path of one of the user's own uploads, or None (with a flash message)."""
    filename = secure_filename(filename)
    if not filename.startswith(f"{current_user.id}_"):
        flash("You can only view your own analyses.")
        return None
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        flash("File not found. Please upload again.")
        return None
    return path


KIND_LABELS = {"number": "Number", "category": "Category", "date": "Date",
               "text": "Text", "id": "ID / name", "empty": "Empty", "month": "Month"}
STOCK_ORDER = [("Out of stock", "red"), ("Reorder now", "amber"), ("Low", "amber"),
               ("Overstocked", "grey"), ("No sales", "grey")]


@app.route("/report", methods=["GET", "POST"])
@login_required
def report_upload():
    if request.method == "POST":
        filename = save_upload()
        if filename:
            return redirect(url_for("report_view", filename=filename))
        return redirect(url_for("report_upload"))
    return render_template("upload_simple.html", kind="report")


@app.route("/report/<filename>")
@login_required
def report_view(filename):
    path = own_file(filename)
    if path is None:
        return redirect(url_for("report_upload"))
    try:
        r = build_report(path, current_lang())
    except Exception as e:
        flash(f"Could not analyse this file: {e}")
        return redirect(url_for("report_upload"))
    return render_template("report.html", r=r, filename=display_name(secure_filename(filename)),
                           kind_labels=KIND_LABELS)


@app.route("/stock", methods=["GET", "POST"])
@login_required
def stock_upload():
    if request.method == "POST":
        filename = save_upload()
        if filename:
            return redirect(url_for("stock_view", filename=filename))
        return redirect(url_for("stock_upload"))
    return render_template("upload_simple.html", kind="stock")


@app.route("/stock/<filename>")
@login_required
def stock_view(filename):
    path = own_file(filename)
    if path is None:
        return redirect(url_for("stock_upload"))
    try:
        r = build_stock(path, current_lang())
    except Exception as e:
        flash(f"Could not analyse this file: {e}")
        return redirect(url_for("stock_upload"))
    return render_template("stock.html", r=r, filename=display_name(secure_filename(filename)),
                           order=STOCK_ORDER)


@app.route("/grow", methods=["GET", "POST"])
def grow_page():
    lang = current_lang()
    i = 1 if lang == "ta" else 0
    form = {"name": "", "btype": "shop", "goal": "new", "area": "", "problem": ""}
    plan = None
    if request.method == "POST":
        for k in form:
            form[k] = request.form.get(k, "").strip()[:300]
        plan = advise(form["name"], form["btype"], form["goal"], form["area"], form["problem"], lang)
    return render_template("grow.html", form=form, plan=plan,
                           types=[(k, v[i]) for k, v in TYPES.items()],
                           goals=[(k, v[i]) for k, v in GOALS.items()],
                           copied=tr("Copied!", lang))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
