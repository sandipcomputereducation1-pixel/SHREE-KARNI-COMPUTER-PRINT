import os, sqlite3, uuid, qrcode
from pathlib import Path
from io import BytesIO
from datetime import datetime
from flask import Flask, request, redirect, url_for, send_file, send_from_directory, render_template_string, abort, session, jsonify
from werkzeug.utils import secure_filename

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)
DB = os.environ.get("DATABASE_PATH", str(BASE / "orders.db"))
SHOP = "Shree Karni Computer Dalot"
CONTACT = "7891411425 / 7339871128"
UPI_ID = os.environ.get("UPI_ID", "7891411425@ptyes")
UPI_NAME = "Shree Karni Computer"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CHANGE-THIS-PASSWORD")
AGENT_TOKEN = os.environ.get("AGENT_TOKEN", "CHANGE-THIS-AGENT-TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://127.0.0.1:5000").rstrip("/")
ALLOWED = {".pdf", ".jpg", ".jpeg", ".png"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with connect() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
      id TEXT PRIMARY KEY, filename TEXT NOT NULL, original TEXT NOT NULL,
      customer TEXT, color TEXT, paper TEXT, copies INTEGER, payment TEXT,
      amount REAL DEFAULT 0, payment_status TEXT DEFAULT 'Unverified',
      status TEXT DEFAULT 'New', created TEXT)""")

CSS = """
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#f2f5f9;color:#172033;font:16px Arial}
header{background:#102b50;color:#fff;text-align:center;padding:22px 12px}
header h1{margin:0;font-size:23px}header p{margin:7px 0 0;color:#dce9f8}
main{max-width:900px;margin:22px auto;padding:0 14px}.card{background:white;padding:20px;border-radius:15px;margin:14px 0;box-shadow:0 3px 16px #102b5012}
h2{color:#102b50;margin-top:0}.btn{background:#087b55;color:white;border:0;border-radius:9px;padding:12px 16px;text-decoration:none;display:inline-block;font-weight:bold;cursor:pointer}
.btn.alt{background:#102b50}input,select{width:100%;padding:12px;margin:7px 0 14px;border:1px solid #cbd5e1;border-radius:8px}
label{font-weight:bold}.muted{color:#64748b;font-size:13px}.row{display:flex;gap:12px;flex-wrap:wrap}.row>div{flex:1;min-width:160px}
table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:9px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}
.tag{display:inline-block;background:#e8f7ef;color:#087b55;padding:4px 8px;border-radius:20px;font-size:12px}
footer{text-align:center;color:#64748b;padding:24px;font-size:13px}
</style>
"""
def page(body, title="Print by QR"):
    return render_template_string(f"""<!doctype html><html lang="hi"><meta charset="utf-8"><title>{title}</title>{CSS}
    <header><h1>SHREE KARNI COMPUTER</h1><p>DALOT • PRINT BY QR</p></header><main>{body}</main>
    <footer>{CONTACT}<br>Scan • Upload • Print</footer></html>""")

def upi_uri():
    from urllib.parse import urlencode
    return "upi://pay?" + urlencode({"pa": UPI_ID, "pn": UPI_NAME, "cu": "INR"})

@app.get("/")
def home():
    body = f"""
    <section class="card"><h2>Print by QR</h2><p>मोबाइल से PDF या फोटो भेजें। दुकान पर फाइल Preview करके ही प्रिंट करें।</p>
    <a class="btn" href="/upload">Customer Print</a> <a class="btn alt" href="/admin">Shop Dashboard</a></section>
    <section class="card"><h2>Customer QR Code</h2><img src="/qr.png" width="210" alt="QR Code">
    <p><a class="btn" href="/qr.png">QR डाउनलोड करें</a></p><p class="muted">पब्लिक QR के लिए PUBLIC_URL को अपनी HTTPS वेबसाइट के पते पर सेट करें।</p></section>
    <section class="card"><h2>UPI Payment</h2><p><b>{UPI_ID}</b></p><a class="btn" href="{upi_uri()}">UPI App खोलें</a>
    <p class="muted">भुगतान दुकान पर अपने UPI ऐप में प्राप्ति जाँचकर ही Paid मार्क करें।</p></section>"""
    return page(body)

@app.get("/qr.png")
def qr():
    im = qrcode.make(PUBLIC_URL + "/upload")
    out = BytesIO(); im.save(out, format="PNG"); out.seek(0)
    return send_file(out, mimetype="image/png")

FORM = """
<section class="card"><h2>मोबाइल से प्रिंट भेजें</h2>
<form method="post" enctype="multipart/form-data">
<label>PDF / फोटो चुनें</label><input type="file" name="file" accept=".pdf,.jpg,.jpeg,.png" required>
<div class="row"><div><label>प्रिंट प्रकार</label><select name="color"><option>Black & White</option><option>Colour</option></select></div>
<div><label>पेपर साइज</label><select name="paper"><option>A4</option><option>4x6 Photo</option><option>Other</option></select></div></div>
<div class="row"><div><label>Copies</label><input name="copies" type="number" min="1" max="100" value="1" required></div>
<div><label>नाम / मोबाइल (वैकल्पिक)</label><input name="customer" placeholder="नाम या मोबाइल"></div></div>
<label>भुगतान का तरीका</label><select name="payment"><option>UPI</option><option>Cash at shop</option></select>
<button class="btn">ऑर्डर भेजें</button></form>
<p class="muted">PDF/JPG/PNG • अधिकतम 20 MB • अभी भुगतान की ऑनलाइन पुष्टि नहीं होती।</p></section>
"""
@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "GET":
        return page(FORM, "Customer Print")
    f = request.files.get("file")
    if not f or not f.filename:
        return page("<section class='card'>कृपया फाइल चुनें।</section>")
    ext = Path(secure_filename(f.filename)).suffix.lower()
    if ext not in ALLOWED:
        return page("<section class='card'>केवल PDF/JPG/PNG फाइल स्वीकार है।</section>")
    f.seek(0, 2); size = f.tell(); f.seek(0)
    if size > 20 * 1024 * 1024:
        return page("<section class='card'>फाइल 20 MB से कम रखें।</section>")
    oid = uuid.uuid4().hex[:8].upper()
    filename = oid + ext
    f.save(UPLOADS / filename)
    copies = max(1, min(100, int(request.form.get("copies", "1") or 1)))
    with connect() as c:
        c.execute("INSERT INTO orders(id,filename,original,customer,color,paper,copies,payment,status,created) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (oid, filename, secure_filename(f.filename), request.form.get("customer",""),
             request.form.get("color","Black & White"), request.form.get("paper","A4"),
             copies, request.form.get("payment","UPI"), "New",
             datetime.now().strftime("%d-%m-%Y %I:%M %p")))
    return page(f"""<section class="card"><h2>ऑर्डर सफलतापूर्वक भेज दिया गया!</h2>
    <p>आपका Order ID: <b>{oid}</b></p><p>दुकान पर यह Order ID बताएं। भुगतान UPI या Cash से दुकान पर कर सकते हैं।</p>
    <a class="btn" href="/">Home</a></section>""", "Order Received")

def admin_required():
    return session.get("admin_ok") is True

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") != ADMIN_PASSWORD:
            return page("<section class='card'>गलत पासवर्ड। <a href='/admin'>फिर प्रयास करें</a></section>")
        session["admin_ok"] = True
        return redirect("/admin")
    if not admin_required():
        return page("<section class='card'><h2>Shop Admin Login</h2><form method='post'><label>Admin Password</label><input type='password' name='password' required><button class='btn'>Login</button></form></section>")
    with connect() as c:
        rows = c.execute("SELECT * FROM orders ORDER BY rowid DESC").fetchall()
    trs = ""
    for r in rows:
        trs += f"""<tr><td><b>{r['id']}</b><br><span class='muted'>{r['created']}</span></td>
        <td>{r['original']}<br>{r['color']} • {r['paper']} • {r['copies']} copies</td>
        <td>{r['payment']}<br>Payment: {r['payment_status']}<br>Order: {r['status']}</td>
        <td><a href='/preview/{r['id']}'>Preview / Print</a><br><a href='/mark/{r['id']}/paid'>Mark Paid</a><br><a href='/mark/{r['id']}/done'>Mark Done</a></td></tr>"""
    body = f"""<section class="card"><h2>Shop Dashboard</h2><p>पहले Preview करें, फिर Windows Print दबाएँ। भुगतान अपने UPI ऐप में जाँचने के बाद ही Paid करें।</p>
    <div style="overflow-x:auto"><table><tr><th>Order</th><th>Print Details</th><th>Payment / Status</th><th>Actions</th></tr>{trs or '<tr><td colspan=4>अभी कोई ऑर्डर नहीं है।</td></tr>'}</table></div>
    <p><a href='/logout'>Logout</a></p></section>"""
    return page(body, "Shop Dashboard")

@app.get("/preview/<oid>")
def preview(oid):
    if not admin_required(): abort(401)
    with connect() as c:
        r = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not r: abort(404)
    link = url_for("order_file", oid=oid)
    body = f"""<section class="card"><h2>Order {oid} – Preview</h2>
    <p><b>File:</b> {r['original']} | <b>Print:</b> {r['color']} | <b>Paper:</b> {r['paper']} | <b>Copies:</b> {r['copies']}</p>
    <p><a class="btn" href="{link}" target="_blank">फाइल खोलें / Preview</a></p>
    <p>फाइल खुलने के बाद PDF/Image viewer में Print दबाएँ और Canon PIXMA G3012 चुनें।</p>
    <p><a class="btn alt" href="/admin">Dashboard पर वापस</a></p></section>"""
    return page(body, "Preview")

@app.get("/order-file/<oid>")
def order_file(oid):
    if not admin_required(): abort(401)
    with connect() as c:
        r = c.execute("SELECT filename FROM orders WHERE id=?", (oid,)).fetchone()
    if not r: abort(404)
    return send_from_directory(UPLOADS, r["filename"], as_attachment=False)

@app.get("/mark/<oid>/<kind>")
def mark(oid, kind):
    if not admin_required(): abort(401)
    if kind not in {"paid", "done"}: abort(400)
    with connect() as c:
        if kind == "paid":
            c.execute("UPDATE orders SET payment_status='Verified by operator' WHERE id=?", (oid,))
        else:
            c.execute("UPDATE orders SET status='Done' WHERE id=?", (oid,))
    return redirect("/admin")

@app.get("/logout")
def logout():
    session.clear()
    return redirect("/admin")

# Windows print agent API. The agent fetches NEW jobs, downloads each once, and opens preview locally.
def agent_auth():
    return request.headers.get("X-Agent-Token") == AGENT_TOKEN

@app.get("/api/agent/jobs")
def agent_jobs():
    if not agent_auth(): abort(401)
    with connect() as c:
        rows = c.execute("SELECT id,original,color,paper,copies,created FROM orders WHERE status='New' ORDER BY rowid ASC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/agent/file/<oid>")
def agent_file(oid):
    if not agent_auth(): abort(401)
    with connect() as c:
        r = c.execute("SELECT filename FROM orders WHERE id=?", (oid,)).fetchone()
    if not r: abort(404)
    return send_from_directory(UPLOADS, r["filename"], as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
