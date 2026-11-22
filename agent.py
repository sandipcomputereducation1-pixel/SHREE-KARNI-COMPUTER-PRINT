"""
Shree Karni Computer – Windows Print Preview Agent
Polls your hosted Print by QR server and downloads each new order once.
It opens the file for operator preview. It DOES NOT print automatically.
"""
import os, time, json, hashlib, webbrowser, subprocess, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SERVER = os.environ.get("PRINT_SERVER_URL", "").rstrip("/")
TOKEN = os.environ.get("AGENT_TOKEN", "")
FOLDER = Path(__file__).parent / "received_orders"
FOLDER.mkdir(exist_ok=True)
SEEN_FILE = FOLDER / "seen_orders.json"
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "15"))

def seen():
    try: return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    except Exception: return set()

def save_seen(items):
    SEEN_FILE.write_text(json.dumps(sorted(items), indent=2), encoding="utf-8")

def get_json(path):
    req = Request(SERVER + path, headers={"X-Agent-Token": TOKEN})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def download(oid, filename):
    req = Request(SERVER + "/api/agent/file/" + oid, headers={"X-Agent-Token": TOKEN})
    with urlopen(req, timeout=60) as r:
        data = r.read()
    suffix = Path(filename).suffix or ".pdf"
    dest = FOLDER / (oid + suffix)
    dest.write_bytes(data)
    return dest

def open_file(path):
    if sys.platform == "win32":
        os.startfile(str(path))
    else:
        webbrowser.open(path.as_uri())

def main():
    if not SERVER or not TOKEN:
        print("Please set PRINT_SERVER_URL and AGENT_TOKEN first.")
        input("Press Enter to exit...")
        return
    print("Shree Karni Print Preview Agent started.")
    print("New orders will open for preview. No automatic printing.")
    done = seen()
    while True:
        try:
            for job in get_json("/api/agent/jobs"):
                oid = job["id"]
                if oid in done: continue
                path = download(oid, job.get("original", "order.pdf"))
                print(f"New order {oid}: {job.get('original')} | {job.get('color')} | {job.get('paper')} | copies {job.get('copies')}")
                open_file(path)
                done.add(oid)
                save_seen(done)
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("Agent stopped.")
            break
        except (URLError, HTTPError, TimeoutError, OSError, ValueError) as e:
            print("Connection/problem:", e)
            time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
