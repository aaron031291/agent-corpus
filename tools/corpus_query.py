"""corpus_query.py — the corpus verification gate.

Query the Grace dataset catalog before claiming prior art or guessing.
Usage:
  python tools/corpus_query.py list                     # all datasets
  python tools/corpus_query.py show <name>              # one dataset detail
  python tools/corpus_query.py search <text>            # search names/hints/notes
  python tools/corpus_query.py sql "<SELECT ...>"       # raw read-only SQL
  python tools/corpus_query.py check "<claim>" --dataset <name> --result "<what found>"
                                                    # log a verification
DB: corpus/catalog.db (build with tools/build_catalog.py)
"""
import os, sqlite3, sys

DB = os.path.join(os.path.dirname(__file__), "..", "corpus", "catalog.db")

def conn():
    if not os.path.exists(DB):
        sys.exit("catalog.db missing — run tools/build_catalog.py first")
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def fmt_size(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024 or unit == "TB":
            return f"{b:.1f}{unit}" if unit != "B" else f"{b}B"
        b /= 1024

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    cmd = args[0]
    con = conn()

    if cmd == "list":
        for r in con.execute("SELECT name,status,format,license,query_hint,size_bytes FROM datasets ORDER BY name"):
            print(f"{r['name']:28s} {r['status']:8s} {fmt_size(r['size_bytes']):>10s}  {r['query_hint']}")

    elif cmd == "show" and len(args) > 1:
        r = con.execute("SELECT * FROM datasets WHERE name LIKE ?", (f"%{args[1]}%",)).fetchone()
        if not r:
            print("not found"); return
        for k in r.keys():
            print(f"{k}: {r[k]}")
        print("\nartifacts:")
        for a in con.execute("SELECT kind,path FROM artifacts WHERE dataset_id=? ORDER BY path LIMIT 60", (r["id"],)):
            print(f"  [{a['kind']}] {a['path']}")

    elif cmd == "search" and len(args) > 1:
        q = f"%{' '.join(args[1:])}%"
        for r in con.execute("""SELECT name,status,notes,query_hint FROM datasets
            WHERE name LIKE ? OR notes LIKE ? OR query_hint LIKE ? OR source LIKE ?""",
            (q, q, q, q)):
            print(f"{r['name']} [{r['status']}]\n  {r['notes']}\n  hint: {r['query_hint']}\n")

    elif cmd == "sql" and len(args) > 1:
        q = " ".join(args[1:]).strip().rstrip(";")
        if not q.lower().startswith(("select", "with", "pragma")):
            sys.exit("read-only: SELECT/WITH/PRAGMA only")
        for row in con.execute(q):
            print(" | ".join(str(x) for x in row))

    elif cmd == "check":
        # check "claim text" --dataset name --result "summary"
        claim = args[1] if len(args) > 1 else ""
        ds = res = ""
        i = 2
        while i < len(args):
            if args[i] == "--dataset": ds = args[i+1]; i += 2
            elif args[i] == "--result": res = args[i+1]; i += 2
            else: i += 1
        con.execute("INSERT INTO claims_checked(agent,claim,dataset,result_summary,verified) VALUES(?,?,?,?,1)",
                    ("devin", claim, ds, res))
        con.commit()
        print("logged to claims_checked")

    else:
        print(__doc__)
    con.close()

if __name__ == "__main__":
    main()
