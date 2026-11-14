"""corpus_query.py — the corpus verification gate.

Query the Grace dataset catalog before claiming prior art or guessing.
Usage:
  python tools/corpus_query.py list                     # all datasets
  python tools/corpus_query.py show <name>              # one dataset detail
  python tools/corpus_query.py search <text>            # search names/hints/notes
  python tools/corpus_query.py sql "<SELECT ...>"       # raw read-only SQL on catalog
  python tools/corpus_query.py data <dataset> "<SQL>"   # query INSIDE a dataset (duckdb)
  python tools/corpus_query.py data <dataset> --tables  # list files + schema
  python tools/corpus_query.py data <dataset> --limit N # row cap (default 1000)
  python tools/corpus_query.py check "<claim>" --dataset <name> --result "<what found>"
                                                    # log a verification
DB: corpus/catalog.db (build with tools/build_catalog.py)
"""
import os, sqlite3, sys

EXTS = (".parquet", ".jsonl", ".ndjson", ".csv")
DATA_EXTS = {".parquet": "parquet", ".jsonl": "json", ".ndjson": "json", ".csv": "csv"}

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

    elif cmd == "data" and len(args) > 1:
        ds_name = args[1]
        row = con.execute("SELECT local_path,format FROM datasets WHERE name LIKE ?",
                          (f"%{ds_name}%",)).fetchone()
        if not row:
            sys.exit(f"dataset '{ds_name}' not in catalog — try: list / search")
        root = row["local_path"] or ""
        if not root or not os.path.isdir(root):
            sys.exit(f"local_path missing or not a dir: {root}")
        files = []
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in (".cache", ".git", "__pycache__")]
            for f in fn:
                ext = os.path.splitext(f)[1].lower()
                if ext in DATA_EXTS:
                    files.append(os.path.join(dp, f))
        if not files:
            sys.exit(f"no tabular files (.parquet/.jsonl/.csv) under {root} — "
                     f"dataset may be repo/archive-only; extract first")
        # group by format, prefer parquet > jsonl > csv
        by_fmt = {}
        for f in files:
            by_fmt.setdefault(DATA_EXTS[os.path.splitext(f)[1].lower()], []).append(f)
        fmt = next((k for k in ("parquet", "json", "csv") if k in by_fmt), None)
        flist = by_fmt[fmt]
        print(f"# dataset={ds_name} format={fmt} files={len(flist)}", file=sys.stderr)

        import duckdb
        d = duckdb.connect()
        def glob_list(paths):
            # duckdb globs; quote each path
            return "[" + ", ".join("'" + p.replace("'", "''") + "'" for p in paths[:500]) + "]"
        if args[2:] == ["--tables"] or (len(args) > 2 and args[2] == "--tables"):
            if fmt == "parquet":
                src = f"read_parquet({glob_list(flist)}, union_by_name=true)"
            elif fmt == "json":
                src = f"read_json_auto({glob_list(flist)}, union_by_name=true)"
            else:
                src = f"read_csv_auto({glob_list(flist)}, union_by_name=true)"
            for r in d.execute(f"DESCRIBE SELECT * FROM {src}").fetchall():
                print(f"{r[0]:30s} {r[1]}")
            return
        limit = 1000
        sql_parts = []
        i = 2
        while i < len(args):
            if args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1]); i += 2
            else:
                sql_parts.append(args[i]); i += 1
        sql = " ".join(sql_parts).strip().rstrip(";")
        if not sql.lower().startswith(("select", "with")):
            sys.exit("read-only: SELECT/WITH only")
        if fmt == "parquet":
            src = f"read_parquet({glob_list(flist)}, union_by_name=true)"
        elif fmt == "json":
            src = f"read_json_auto({glob_list(flist)}, union_by_name=true)"
        else:
            src = f"read_csv_auto({glob_list(flist)}, union_by_name=true)"
        d.execute(f"CREATE OR REPLACE VIEW data AS SELECT * FROM {src}")
        res = d.execute(sql + f" LIMIT {limit}")
        cols = [c[0] for c in res.description]
        print(" | ".join(cols))
        print("-+-".join("-" * len(c) for c in cols))
        n = 0
        for row in res.fetchall():
            print(" | ".join("" if v is None else str(v)[:200] for v in row))
            n += 1
        print(f"-- {n} rows (limit {limit})", file=sys.stderr)
        return

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
