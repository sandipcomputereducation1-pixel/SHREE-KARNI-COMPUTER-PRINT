
import os
import re
import hmac
import uuid
import sqlite3
import qrcode

from pathlib import Path
from io import BytesIO
from datetime import datetime
from urllib.parse import urlencode
from functools import wraps
from html import escape

from flask import (
    Flask, request, redirect, url_for,
    send_file, send_from_directory,
    render_template_string, abort,
    session, jsonify
)

from werkzeug.utils import secure_filename


# ==========================================
# SHREE KARNI COMPUTER DALOT
# PRINT BY QR SYSTEM
# ==========================================

BASE = Path(__file__).resolve().parent

UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)

DB = os.environ.get(
    "DATABASE_PATH",
    str(BASE / "orders.db")
)

SHOP = "Shree Karni Computer Dalot"
CONTACT = "7891411425 / 7339871128"

UPI_ID = os.environ.get(
    "UPI_ID",
    "7891411425@ptyes"
)

UPI_NAME = "Shree Karni Computer"

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "CHANGE-THIS-PASSWORD"
)

AGENT_TOKEN = os.environ.get(
    "AGENT_TOKEN",
    "CHANGE-THIS-AGENT-TOKEN"
)

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "CHANGE-THIS-SECRET-KEY"
)

PUBLIC_URL = os.environ.get(
    "PUBLIC_URL",
    "http://127.0.0.1:5000"
).rstrip("/")

ALLOWED = {".pdf", ".jpg", ".jpeg", ".png"}

MAX_SIZE = 20 * 1024 * 1024

app = Flask(__name__)

app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE


# ==========================================
# DATABASE
# ==========================================

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db


def init_db():

    with connect() as db:

        db.execute("""
        CREATE TABLE IF NOT EXISTS orders(

            id TEXT PRIMARY KEY,

            filename TEXT NOT NULL,

            original TEXT NOT NULL,

            customer TEXT,

            color TEXT,

            paper TEXT,

            copies INTEGER,

            payment TEXT,

            amount REAL DEFAULT 0,

            payment_status TEXT DEFAULT 'Unverified',

            status TEXT DEFAULT 'New',

            created TEXT

        )
        """)


init_db()


# ==========================================
# DESIGN / CSS
# ==========================================

CSS = """
<meta name="viewport" content="width=device-width,initial-scale=1">

<style>

* {
    box-sizing:border-box;
}

body {
    margin:0;
    background:#f1f5f9;
    color:#172033;
    font-family:Arial,sans-serif;
}

header {
    background:linear-gradient(120deg,#071d38,#174b80);
    color:white;
    padding:30px 15px;
    text-align:center;
}

header h1 {
    margin:0;
    font-size:28px;
    letter-spacing:1px;
}

header p {
    color:#dbeafe;
    margin:8px 0 0;
}

main {
    max-width:1050px;
    margin:25px auto;
    padding:0 15px;
}

.card {
    background:white;
    padding:23px;
    border-radius:16px;
    margin-bottom:20px;
    box-shadow:0 5px 22px #102b5010;
}

h2 {
    color:#12345b;
    margin-top:0;
}

.hero {
    background:linear-gradient(130deg,#102b50,#087b75);
    color:white;
    padding:35px 25px;
    border-radius:18px;
}

.hero h2 {
    color:white;
    font-size:30px;
}

.hero p {
    line-height:1.7;
}

.btn {
    background:#07845d;
    color:white;
    padding:13px 18px;
    border:0;
    border-radius:9px;
    text-decoration:none;
    display:inline-block;
    font-weight:bold;
    cursor:pointer;
    margin:5px 3px;
}

.btn:hover {
    opacity:.9;
}

.btn.blue {
    background:#123b68;
}

.btn.red {
    background:#c0392b;
}

input,select {
    width:100%;
    padding:13px;
    border:1px solid #cbd5e1;
    border-radius:9px;
    margin:8px 0 17px;
    background:white;
}

label {
    font-weight:bold;
}

.row {
    display:flex;
    gap:15px;
    flex-wrap:wrap;
}

.row>div {
    flex:1;
    min-width:180px;
}

.grid {
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
    gap:15px;
}

.feature {
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:18px;
}

.feature h3 {
    color:#123b68;
    margin-top:0;
}

.muted {
    font-size:13px;
    color:#64748b;
}

.tag {
    background:#e4f8ed;
    color:#087b55;
    padding:5px 10px;
    border-radius:20px;
    font-size:12px;
}

table {
    width:100%;
    border-collapse:collapse;
    font-size:14px;
}

td,th {
    padding:12px;
    border-bottom:1px solid #e2e8f0;
    text-align:left;
    vertical-align:top;
}

footer {
    text-align:center;
    background:#102b50;
    color:white;
    padding:25px;
    margin-top:35px;
}

.qr {
    width:220px;
    max-width:100%;
}

@media(max-width:600px) {
    header h1 {font-size:22px;}
    .hero h2 {font-size:24px;}
    .card {padding:17px;}
    table {font-size:12px;}
}

</style>
"""


# ==========================================
# PAGE TEMPLATE
# ==========================================

def page(body, title="Print by QR"):

    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="hi">

        <head>
        <meta charset="UTF-8">
        <title>{{ title }}</title>
        """ + CSS + """
        </head>

        <body>

        <header>
            <h1>SHREE KARNI COMPUTER</h1>
            <p>DALOT • PRINT BY QR</p>
            <p>Learn • Grow • Succeed</p>
        </header>

        <main>
            {{ body|safe }}
        </main>

        <footer>
            <b>SHREE KARNI COMPUTER DALOT</b>
            <br>
            {{ contact }}
            <br>
            Scan • Upload • Print
        </footer>

        </body>
        </html>
        """,
        body=body,
        title=title,
        contact=CONTACT
    )


# ==========================================
# UPI PAYMENT
# ==========================================

def upi_uri():

    return "upi://pay?" + urlencode({

        "pa": UPI_ID,
        "pn": UPI_NAME,
        "cu": "INR"

    })


# ==========================================
# HOME PAGE
# ==========================================

@app.get("/")
def home():

    body = f"""

    <section class="hero">

        <h2>ONLINE PRINT SERVICE</h2>

        <h3>Print Made Easy!</h3>

        <p>
        मोबाइल से PDF या फोटो भेजें
        और दुकान पर आसानी से प्रिंट प्राप्त करें।
        </p>

        <a class="btn" href="/upload">
            CUSTOMER PRINT
        </a>

        <a class="btn blue" href="/admin">
            SHOP DASHBOARD
        </a>

    </section>


    <section class="card">

        <h2>हमारी सुविधाएँ</h2>

        <div class="grid">

            <div class="feature">
                <h3>PDF Print</h3>
                <p>मोबाइल से PDF भेजें।</p>
            </div>

            <div class="feature">
                <h3>Photo Print</h3>
                <p>JPG और PNG फोटो प्रिंट।</p>
            </div>

            <div class="feature">
                <h3>Colour Print</h3>
                <p>Colour और Black & White।</p>
            </div>

            <div class="feature">
                <h3>Quick Service</h3>
                <p>QR Scan करके ऑर्डर भेजें।</p>
            </div>

        </div>

    </section>


    <section class="card" style="text-align:center">

        <h2>SCAN & UPLOAD</h2>

        <img class="qr" src="/qr.png">

        <p>QR Code स्कैन करके फाइल भेजें।</p>

        <a class="btn" href="/qr.png">
            Download QR Code
        </a>

    </section>


    <section class="card">

        <h2>UPI Payment</h2>

        <p><b>{escape(UPI_ID)}</b></p>

        <a class="btn" href="{escape(upi_uri())}">
            Open UPI App
        </a>

        <p class="muted">
        भुगतान की पुष्टि दुकान पर की जाएगी।
        </p>

    </section>

    """

    return page(body, "Shree Karni Computer | Print by QR")


# ==========================================
# QR CODE
# ==========================================

@app.get("/qr.png")
def qr():

    im = qrcode.make(PUBLIC_URL + "/upload")

    out = BytesIO()

    im.save(out, format="PNG")

    out.seek(0)

    return send_file(out, mimetype="image/png")


# ==========================================
# CUSTOMER UPLOAD FORM
# ==========================================

FORM = """

<section class="card">

<h2>Customer Print Upload</h2>

<p>मोबाइल से PDF या फोटो अपलोड करें।</p>

<form method="post" enctype="multipart/form-data">

<label>PDF / Photo चुनें</label>

<input
type="file"
name="file"
accept=".pdf,.jpg,.jpeg,.png"
required
>

<div class="row">

<div>
<label>Print Type</label>

<select name="color">
<option>Black & White</option>
<option>Colour</option>
</select>
</div>

<div>
<label>Paper Size</label>

<select name="paper">
<option>A4</option>
<option>4x6 Photo</option>
<option>Other</option>
</select>
</div>

</div>

<div class="row">

<div>
<label>Copies</label>

<input
type="number"
name="copies"
min="1"
max="100"
value="1"
required
>
</div>

<div>
<label>Name / Mobile</label>

<input
name="customer"
maxlength="100"
placeholder="नाम या मोबाइल"
>
</div>

</div>

<label>Payment Method</label>

<select name="payment">
<option>UPI</option>
<option>Cash at shop</option>
</select>

<button class="btn">SUBMIT ORDER</button>

</form>

<p class="muted">
PDF/JPG/PNG • Maximum 20 MB
</p>

</section>

"""


# ==========================================
# CUSTOMER UPLOAD
# ==========================================

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "GET":

        return page(FORM, "Customer Upload")

    f = request.files.get("file")

    if not f or not f.filename:

        return page(
            "<section class='card'>कृपया फाइल चुनें।</section>"
        )

    original = secure_filename(f.filename)

    ext = Path(original).suffix.lower()

    if ext not in ALLOWED:

        return page(
            "<section class='card'>केवल PDF/JPG/PNG स्वीकार हैं।</section>"
        )

    f.seek(0, 2)

    size = f.tell()

    f.seek(0)

    if size <= 0 or size > MAX_SIZE:

        return page(
            "<section class='card'>फाइल 20 MB से कम रखें।</section>"
        )

    try:

        copies = int(request.form.get("copies", "1"))

    except ValueError:

        copies = 1

    copies = max(1, min(100, copies))

    oid = uuid.uuid4().hex[:8].upper()

    filename = oid + ext

    f.save(UPLOADS / filename)

    customer = request.form.get("customer", "")[:100]

    color = request.form.get("color", "Black & White")

    if color not in {"Black & White", "Colour"}:
        color = "Black & White"

    paper = request.form.get("paper", "A4")

    if paper not in {"A4", "4x6 Photo", "Other"}:
        paper = "A4"

    payment = request.form.get("payment", "UPI")

    if payment not in {"UPI", "Cash at shop"}:
        payment = "UPI"

    created = datetime.now().strftime(
        "%d-%m-%Y %I:%M %p"
    )

    try:

        with connect() as db:

            db.execute("""
            INSERT INTO orders
            (
                id,filename,original,customer,
                color,paper,copies,payment,
                status,created
            )
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """, (
                oid,
                filename,
                original,
                customer,
                color,
                paper,
                copies,
                payment,
                "New",
                created
            ))

    except Exception:

        (UPLOADS / filename).unlink(missing_ok=True)

        raise

    return page(f"""

    <section class="card">

    <h2>Order Successfully Submitted!</h2>

    <p>आपका ऑर्डर सफलतापूर्वक भेज दिया गया है।</p>

    <h2>Order ID: {oid}</h2>

    <p>दुकान पर अपना Order ID बताएं।</p>

    <p>Payment: {escape(payment)}</p>

    <p class="tag">Order Status: New</p>

    <a class="btn" href="/">HOME</a>

    </section>

    """, "Order Received")


# ==========================================
# ADMIN LOGIN
# ==========================================

def admin_required():

    return session.get("admin_ok") is True


def admin_login_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if not admin_required():
            abort(401)

        return fn(*args, **kwargs)

    return wrapper


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        password = request.form.get("password", "")

        if hmac.compare_digest(
            password,
            ADMIN_PASSWORD
        ):

            session.clear()

            session["admin_ok"] = True

            return redirect("/admin")

        return page("""
        <section class="card">
        <h2>गलत पासवर्ड!</h2>
        <a href="/admin">फिर प्रयास करें</a>
        </section>
        """)

    if not admin_required():

        return page("""

        <section class="card">

        <h2>SHOP ADMIN LOGIN</h2>

        <form method="post">

        <label>Admin Password</label>

        <input
        type="password"
        name="password"
        required
        >

        <button class="btn">LOGIN</button>

        </form>

        </section>

        """, "Admin Login")

    with connect() as db:

        rows = db.execute(
            "SELECT * FROM orders ORDER BY rowid DESC"
        ).fetchall()

    trs = ""

    for r in rows:

        oid = escape(r["id"])

        trs += f"""

        <tr>

        <td>
        <b>{oid}</b>
        <br>
        <span class="muted">
        {escape(r["created"] or "")}
        </span>
        </td>

        <td>
        {escape(r["original"])}
        <br>
        {escape(r["color"] or "")}
        • {escape(r["paper"] or "")}
        • {r["copies"]} Copies
        <br>
        Customer: {escape(r["customer"] or "")}
        </td>

        <td>
        {escape(r["payment"] or "")}
        <br>
        Payment: {escape(r["payment_status"] or "")}
        <br>
        Order: {escape(r["status"] or "")}
        </td>

        <td>

        <a href="/preview/{oid}">Preview / Print</a>

        <br>

        <form method="post" action="/mark/{oid}/paid">
        <button class="btn">Mark Paid</button>
        </form>

        <form method="post" action="/mark/{oid}/done">
        <button class="btn blue">Mark Done</button>
        </form>

        </td>

        </tr>

        """

    body = f"""

    <section class="card">

    <h2>SHOP DASHBOARD</h2>

    <p>Shree Karni Computer Dalot</p>

    <div class="grid">

    <div class="feature">
    <h3>Total Orders</h3>
    <h2>{len(rows)}</h2>
    </div>

    <div class="feature">
    <h3>New Orders</h3>
    <h2>{sum(1 for r in rows if r['status'] == 'New')}</h2>
    </div>

    <div class="feature">
    <h3>Completed</h3>
    <h2>{sum(1 for r in rows if r['status'] == 'Done')}</h2>
    </div>

    </div>

    <h2>All Orders</h2>

    <div style="overflow-x:auto">

    <table>

    <tr>
    <th>Order</th>
    <th>Print Details</th>
    <th>Payment / Status</th>
    <th>Actions</th>
    </tr>

    {trs or '<tr><td colspan="4">अभी कोई ऑर्डर नहीं है।</td></tr>'}

    </table>

    </div>

    <form method="post" action="/logout">
    <button class="btn red">LOGOUT</button>
    </form>

    </section>

    """

    return page(body, "Shop Dashboard")


# ==========================================
# ORDER PREVIEW
# ==========================================

@app.get("/preview/<oid>")
@admin_login_required
def preview(oid):

    with connect() as db:

        r = db.execute(
            "SELECT * FROM orders WHERE id=?",
            (oid,)
        ).fetchone()

    if not r:
        abort(404)

    body = f"""

    <section class="card">

    <h2>Order {escape(r['id'])} – Preview</h2>

    <p>
    <b>File:</b> {escape(r['original'])}
    </p>

    <p>
    <b>Print:</b> {escape(r['color'] or '')}
    </p>

    <p>
    <b>Paper:</b> {escape(r['paper'] or '')}
    </p>

    <p>
    <b>Copies:</b> {r['copies']}
    </p>

    <p>
    <a class="btn"
    href="/order-file/{escape(r['id'])}"
    target="_blank">
    OPEN FILE / PREVIEW
    </a>
    </p>

    <p>
    फाइल खुलने के बाद Print दबाएँ और
    Canon PIXMA G3012 चुनें।
    </p>

    <a class="btn blue" href="/admin">
    BACK TO DASHBOARD
    </a>

    </section>

    """

    return page(body, "Order Preview")


# ==========================================
# ADMIN FILE DOWNLOAD
# ==========================================

@app.get("/order-file/<oid>")
@admin_login_required
def order_file(oid):

    with connect() as db:

        r = db.execute(
            "SELECT filename FROM orders WHERE id=?",
            (oid,)
        ).fetchone()

    if not r:
        abort(404)

    return send_from_directory(
        UPLOADS,
        r["filename"],
        as_attachment=False
    )


# ==========================================
# MARK PAID / DONE
# ==========================================

@app.post("/mark/<oid>/<kind>")
@admin_login_required
def mark(oid, kind):

    if kind not in {"paid", "done"}:
        abort(400)

    with connect() as db:

        if kind == "paid":

            db.execute("""
            UPDATE orders
            SET payment_status='Verified by operator'
            WHERE id=?
            """, (oid,))

        else:

            db.execute("""
            UPDATE orders
            SET status='Done'
            WHERE id=?
            """, (oid,))

    return redirect("/admin")


# ==========================================
# ADMIN LOGOUT
# ==========================================

@app.post("/logout")
@admin_login_required
def logout():

    session.clear()

    return redirect("/admin")


# ==========================================
# WINDOWS PRINT AGENT AUTHENTICATION
# ==========================================

def agent_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        token = request.headers.get(
            "X-Agent-Token", ""
        )

        if not AGENT_TOKEN or not hmac.compare_digest(
            token,
            AGENT_TOKEN
        ):

            abort(401)

        return fn(*args, **kwargs)

    return wrapper


# ==========================================
# WINDOWS AGENT - GET NEW JOBS
# ==========================================

@app.get("/api/agent/jobs")
@agent_required
def agent_jobs():

    with connect() as db:

        rows = db.execute("""
        SELECT id,original,color,paper,copies,created
        FROM orders
        WHERE status='New'
        ORDER BY rowid ASC
        """).fetchall()

    jobs = []

    for r in rows:

        jobs.append({

            "id": r["id"],

            "filename": r["original"],

            "color": r["color"],

            "paper": r["paper"],

            "copies": r["copies"],

            "created": r["created"],

            "download_url": (
                PUBLIC_URL + "/api/agent/file/" + r["id"]
            )

        })

    return jsonify(jobs)


# ==========================================
# WINDOWS AGENT - DOWNLOAD FILE
# ==========================================

@app.get("/api/agent/file/<oid>")
@agent_required
def agent_file(oid):

    with connect() as db:

        r = db.execute(
            "SELECT filename FROM orders WHERE id=?",
            (oid,)
        ).fetchone()

    if not r:
        abort(404)

    return send_from_directory(
        UPLOADS,
        r["filename"],
        as_attachment=True
    )


# ==========================================
# WINDOWS AGENT - UPDATE STATUS
# ==========================================

@app.post("/api/agent/status")
@agent_required
def agent_status():

    data = request.get_json(silent=True) or {}

    oid = str(data.get("id", ""))

    status = str(data.get("status", ""))

    if status not in {"Printing", "Done", "New"}:
        return jsonify({"error": "Invalid status"}), 400

    with connect() as db:

        cur = db.execute(
            "UPDATE orders SET status=? WHERE id=?",
            (status, oid)
        )

        if cur.rowcount == 0:
            return jsonify({"error": "Order not found"}), 404

    return jsonify({

        "success": True,

        "id": oid,

        "status": status

    })


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return jsonify({

        "status": "online",

        "shop": SHOP,

        "service": "Print by QR",

        "printer": "Canon PIXMA G3012"

    })


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(401)
def unauthorized(e):

    return page("""
    <section class="card">
    <h2>Login Required</h2>
    <a href="/admin">Admin Login</a>
    </section>
    """), 401


@app.errorhandler(404)
def not_found(e):

    return page("""
    <section class="card">
    <h2>404 - Page Not Found</h2>
    <a href="/">Home</a>
    </section>
    """), 404


@app.errorhandler(413)
def too_large(e):

    return page("""
    <section class="card">
    <h2>File बहुत बड़ी है!</h2>
    <p>कृपया 20 MB से छोटी फाइल अपलोड करें।</p>
    <a href="/upload">फिर प्रयास करें</a>
    </section>
    """), 413


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
