"""dataset_status.py — check corpus download jobs.

For each job in catalog.db `jobs` table: measure artifact size, compare
to last check (GROWING/STALLED/DONE/MISSING). Updates last_size/last_check.

Usage: python tools/dataset_status.py [--json]
"""
import os, sqlite3, sys, json
from datetime import datetime, timezone

DB = os.path.join(os.path.dirname(__file__), "..", "corpus", "catalog.db")

def dir_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total

def main():
    as_json = "--json" in sys.argv
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = []
    for j in con.execute("SELECT * FROM jobs ORDER BY name"):
        size = dir_size(j["artifact_path"]) if os.path.exists(j["artifact_path"]) else 0
        exp = j["expected_bytes"]
        prev = j["last_size"] or 0
        if size == 0:
            status = "MISSING"
        elif exp and size >= exp * 0.98:
            status = "DONE"
        elif size > prev:
            status = "GROWING"
        elif prev > 0:
            status = "STALLED?"
        else:
            status = "STARTED"
        con.execute("UPDATE jobs SET last_size=?, last_check=?, status=? WHERE id=?",
                    (size, now, status, j["id"]))
        out.append({"job": j["name"], "status": status,
                    "size_gb": round(size/1e9, 2),
                    "expected_gb": round(exp/1e9, 1) if exp else None,
                    "note": j["note"]})
    con.commit(); con.close()
    if as_json:
        print(json.dumps(out, indent=2))
    else:
        for o in out:
            exp = f"/{o['expected_gb']}GB" if o['expected_gb'] else ""
            print(f"{o['status']:9s} {o['job']:20s} {o['size_gb']:>8.2f}GB{exp:>10s}  {o['note']}")

if __name__ == "__main__":
    main()
