import os
import re
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from io import BytesIO

import qrcode
import fitz
from PIL import Image
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    send_from_directory, flash, jsonify, send_file, abort
)
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE)))
UPLOAD_DIR = DATA_DIR / "uploads"
DB = DATA_DIR / "orders.db"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
UPI_ID = os.environ.get("UPI_ID", "7891411425@ptyes")
SHOP_NAME = "Shree Karni Computer Dalot"
ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
RATES = {
    "A4": 10.0,
    "4×6 Inch": 40.0,
    "ID Card": 50.0,
    "PVC Card 98×54 mm": 50.0,
}

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY, customer_name TEXT, mobile TEXT, print_size TEXT,
            copies INTEGER, payment_mode TEXT, amount REAL, status TEXT,
            filename TEXT, original_name TEXT, created_at TEXT,
            payment_verified INTEGER DEFAULT 0
        )""")
        cols = {row["name"] for row in con.execute("PRAGMA table_info(orders)")}
        if "payment_verified" not in cols:
            con.execute("ALTER TABLE orders ADD COLUMN payment_verified INTEGER DEFAULT 0")

init_db()

def allowed_file(name):
    return Path(name).suffix.lower() in ALLOWED

def admin_required():
    return bool(session.get("admin"))

def safe_order_file(filename):
    # Only serve a basename stored by this application.
    name = Path(filename).name
    if name != filename or name in {"", ".", ".."}:
        abort(404)
    return name

def process_pdf(source_path, destination_path, pages_text="", rotate=0, crop_mm=0):
    src = fitz.open(source_path)
    out = fitz.open()
    total = len(src)
    if total == 0:
        raise ValueError("PDF में कोई पेज नहीं है।")
    selected = []
    if pages_text.strip():
        for part in pages_text.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                start, end = int(a), int(b)
                if start < 1 or end < start or end > total:
                    raise ValueError("PDF Page Range सही नहीं है।")
                selected.extend(range(start - 1, end))
            else:
                n = int(part)
                if n < 1 or n > total:
                    raise ValueError("PDF Page Number सही नहीं है।")
                selected.append(n - 1)
    else:
        selected = list(range(total))
    # Keep order but remove duplicates.
    selected = list(dict.fromkeys(selected))
    for index in selected:
        page = out.new_page(width=src[index].rect.width, height=src[index].rect.height)
        page.show_pdf_page(page.rect, src, index)
        if crop_mm > 0:
            margin = crop_mm * 72 / 25.4
            rect = page.rect
            crop = fitz.Rect(
                min(rect.x0 + margin, rect.x1 - 1),
                min(rect.y0 + margin, rect.y1 - 1),
                max(rect.x1 - margin, rect.x0 + 1),
                max(rect.y1 - margin, rect.y0 + 1),
            )
            page.set_cropbox(crop)
        if rotate:
            page.set_rotation((page.rotation + rotate) % 360)
    out.save(destination_path, garbage=4, deflate=True)
    out.close()
    src.close()

@app.errorhandler(413)
def too_large(_error):
    flash("फाइल 25 MB से बड़ी है। कृपया छोटी फाइल चुनें।")
    return redirect(url_for("upload_page"))

@app.route("/")
def home():
    return redirect(url_for("upload_page"))

@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":
        f = request.files.get("file")
        if not f or not f.filename:
            flash("कृपया फोटो या PDF चुनें।")
            return redirect(url_for("upload_page"))
        if not allowed_file(f.filename):
            flash("केवल JPG, PNG, WEBP और PDF फाइल स्वीकार हैं।")
            return redirect(url_for("upload_page"))

        name = request.form.get("customer_name", "").strip()[:100]
        mobile = re.sub(r"\D", "", request.form.get("mobile", ""))[:15]
        if not name or len(mobile) < 10:
            flash("कृपया ग्राहक का नाम और सही मोबाइल नंबर भरें।")
            return redirect(url_for("upload_page"))

        size = request.form.get("print_size", "A4")
        if size not in RATES:
            flash("कृपया सही Print Size चुनें।")
            return redirect(url_for("upload_page"))
        try:
            copies = max(1, min(100, int(request.form.get("copies", "1"))))
        except (TypeError, ValueError):
            copies = 1
        payment = request.form.get("payment_mode", "Cash")
        if payment not in {"Cash", "UPI"}:
            payment = "Cash"

        original = secure_filename(f.filename) or "customer-file"
        ext = Path(original).suffix.lower()
        order_id = "SK" + datetime.now().strftime("%y%m%d") + uuid.uuid4().hex[:6].upper()
        stored = order_id + ext
        source_path = UPLOAD_DIR / stored
        f.save(source_path)

        # Apply PDF page selection / rotation / crop when the uploaded file is a PDF.
        if ext == ".pdf":
            try:
                pages_text = request.form.get("pdf_pages", "")
                rotate = int(request.form.get("pdf_rotate", "0") or 0) % 360
                if rotate not in {0, 90, 180, 270}:
                    rotate = 0
                crop_mm = max(0, min(20, float(request.form.get("pdf_crop_mm", "0") or 0)))
                if pages_text.strip() or rotate or crop_mm:
                    edited_path = UPLOAD_DIR / (order_id + "-edited.pdf")
                    process_pdf(source_path, edited_path, pages_text, rotate, crop_mm)
                    source_path.unlink(missing_ok=True)
                    source_path = edited_path
                    stored = edited_path.name
            except Exception as exc:
                source_path.unlink(missing_ok=True)
                flash("PDF Edit लागू नहीं हो पाया: " + str(exc))
                return redirect(url_for("upload_page"))

        amount = round(RATES[size] * copies, 2)
        with db() as con:
            con.execute("""INSERT INTO orders
                (id, customer_name, mobile, print_size, copies, payment_mode,
                 amount, status, filename, original_name, created_at, payment_verified)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (order_id, name, mobile, size, copies, payment, amount, "Pending",
                 stored, original, datetime.now().strftime("%d-%m-%Y %I:%M %p"), 0))
        return redirect(url_for("order_page", order_id=order_id))

    return render_template("upload.html", upi_id=UPI_ID, shop_name=SHOP_NAME, rates=RATES)

@app.route("/order/<order_id>")
def order_page(order_id):
    with db() as con:
        order = con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        return "Order not found", 404
    return render_template("order.html", order=order, upi_id=UPI_ID)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if not ADMIN_PASSWORD:
            flash("Admin password Render Environment में सेट नहीं है।")
        elif request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASSWORD:
            session.clear()
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            flash("गलत यूज़रनेम या पासवर्ड")
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin")
def admin():
    if not admin_required():
        return redirect(url_for("admin_login"))
    search = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    query = "SELECT * FROM orders WHERE 1=1"
    args = []
    if search:
        query += " AND (id LIKE ? OR customer_name LIKE ? OR mobile LIKE ?)"
        args.extend([f"%{search}%"] * 3)
    if status_filter in {"Pending", "Printing", "Completed"}:
        query += " AND status=?"
        args.append(status_filter)
    query += " ORDER BY rowid DESC"
    with db() as con:
        orders = con.execute(query, args).fetchall()
        summary = con.execute("""SELECT COUNT(*) total,
            COALESCE(SUM(amount),0) revenue,
            SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END) pending,
            SUM(CASE WHEN payment_verified=1 THEN amount ELSE 0 END) verified_amount
            FROM orders""").fetchone()
    return render_template("admin.html", orders=orders, summary=summary,
                           q=search, status_filter=status_filter)

@app.route("/admin/status/<order_id>", methods=["POST"])
def update_status(order_id):
    if not admin_required():
        return jsonify(ok=False), 401
    status = request.form.get("status")
    if status not in {"Pending", "Printing", "Completed"}:
        return jsonify(ok=False, error="Invalid status"), 400
    with db() as con:
        con.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    return redirect(url_for("admin"))

@app.route("/admin/payment/<order_id>", methods=["POST"])
def verify_payment(order_id):
    if not admin_required():
        return jsonify(ok=False), 401
    verified = 1 if request.form.get("verified") == "1" else 0
    with db() as con:
        con.execute("UPDATE orders SET payment_verified=? WHERE id=?", (verified, order_id))
    return redirect(url_for("admin"))

@app.route("/file/<filename>")
def get_file(filename):
    if not admin_required():
        return "Unauthorized", 401
    return send_from_directory(UPLOAD_DIR, safe_order_file(filename), as_attachment=False)

@app.route("/download/<filename>")
def download_file(filename):
    if not admin_required():
        return "Unauthorized", 401
    return send_from_directory(UPLOAD_DIR, safe_order_file(filename), as_attachment=True)

@app.route("/qr.png")
def qr_code():
    img = qrcode.make(request.url_root.rstrip("/") + url_for("upload_page"))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/health")
def health():
    return {"ok": True, "app": "Shree Karni QR Print System"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
