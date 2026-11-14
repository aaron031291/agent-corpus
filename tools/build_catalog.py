"""Build corpus/catalog.db — the index over Desktop\\datasets.

Scans the datasets folder, records per-dataset metadata (format, size,
license, query hints), and creates the claims_checked audit table.
Run: python tools/build_catalog.py
"""
import os, sqlite3, json, subprocess, sys

DATASETS_DIR = r"C:\Users\aaron\Desktop\datasets"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "corpus", "catalog.db")

# name -> (source, format, license, query_hint, notes)
MANIFEST = {
    "Project_CodeNet": ("IBM/Project_CodeNet", "tar.gz + extracted dirs",
        "research use", "metadata/*.csv per problem; data/<problem>/<lang>/s*.ext",
        "13.9M submissions, 4053 problems, 55 langs; Accepted/WrongAnswer labels"),
    "run_bug_run": ("github.com/giganticode/run_bug_run", "repo + .lrz SQLite dump",
        "research", "restore: lrunzip runbugrun.sql.lrz; sqlite3 runbugrun.db",
        "700k executable buggy/fixed pairs, 9 langs, tests+labels+bubblewrap"),
    "code_contests_hf": ("deepmind/code_contests (HF parquet)", "parquet shards",
        "DeepMind research", "data/train-*.parquet, test-*.parquet",
        "AlphaCode dataset: problems + test I/O + correct/incorrect solutions"),
    "CVEfixes": ("Zenodo 10.5281/zenodo.4476563", "zip (12.7GB) + repo",
        "code MIT / data CC BY 4.0", "CVEfixes_v1.0.8.zip -> Code/ per-CVE dirs",
        "12107 vuln-fix commits, 4249 projects, 11873 CVEs, 272 CWEs"),
    "libra-eval": ("github.com/LibrAIResearch/libra-eval", "repo + JSONL datasets",
        "Apache-2.0", "libra_eval/datasets/*.jsonl",
        "LLM safety/capability evals (HarmBench, DoNotAnswer, BBQ, etc.)"),
    "BugsInPy": ("github.com/soarsmu/BugsInPy", "repo",
        "research", "Bugs/ per-project bug dirs",
        "~500 real Python bugs across 17 projects; used by SIG learning bench"),
    "hf_SWE-bench": ("princeton-nlp/SWE-bench", "parquet/json",
        "MIT-ish research", "data/{train,dev,test}-*.parquet",
        "21.5k real GitHub issue->fix instances, FAIL_TO_PASS tests"),
    "hf_SWE-bench_Verified": ("princeton-nlp/SWE-bench_Verified", "parquet",
        "research", "data/*.parquet", "500 human-verified SWE-bench instances"),
    "hf_SWE-bench_Multilingual": ("princeton-nlp/SWE-bench_Multilingual", "parquet",
        "research", "data/*.parquet", "300 instances, 9 languages, 42 repos"),
    "hf_SWE-smith": ("SWE-bench/SWE-smith", "parquet",
        "MIT", "data/train-*.parquet",
        "59k synthetic task instances across 128 repos, executable envs"),
    "hf_Multi-SWE-bench": ("ByteDance-Seed/Multi-SWE-bench", "json/parquet",
        "research", "per-language instance dirs",
        "~1.6k real issues, 7 languages (Java/TS/Go/Rust/C/C++/PHP)"),
    "hf_SWE-Gym": ("SWE-Gym/SWE-Gym", "parquet/json",
        "MIT", "data + trajectories",
        "~2.4k instances + agent trajectories"),
    "hf_ManySStuBs4J": ("claudios/ManySStuBs4J", "json/parquet",
        "research", "data files",
        "~150k real Java bug-fix pairs (single-statement bugs)"),
    "hf_bugswarm_maven": ("islamham/bugswarm_maven (BugSwarm mirror)", "json",
        "research", "records",
        "reproducible Java/Maven build->fix bugs"),
    "hf_bugswarm_gradle": ("islamham/bugswarm_gradle", "json", "research", "records", "BugSwarm gradle subset"),
    "hf_bugswarm_ant": ("islamham/bugswarm_ant", "json", "research", "records", "BugSwarm ant subset"),
    "hf_bugswarm_python": ("islamham/bugswarm_python", "json", "research", "records", "BugSwarm python subset"),
    "hf_devign": ("DetectVul/devign", "json/parquet", "research",
        "function-level records", "27k C functions labeled vuln/not-vuln"),
    "hf_PrimeVul": ("colin/PrimeVul", "json/parquet", "research",
        "function-level records", "~7k real CVE-linked vulnerable functions"),
    "hf_bigvul": ("bstee615/bigvul", "json/parquet", "research",
        "function-level records", "3,754 CVEs with code context"),
    "hf_the-stack-smol-xl": ("bigcode/the-stack-smol-xl", "json per lang",
        "permissive-licensed subset", "data/<lang>/data.json (has content!)",
        "Stack sample ~89 langs WITH actual code content + repo metadata"),
    "hf_the-stack-v2": ("bigcode/the-stack-v2", "parquet index",
        "gated: HF account + license", "data/<Lang>/train-*.parquet",
        "INDEX ONLY (blob/content IDs); code lives in SWH S3 — needs INRIA agreement"),
    "hf_codeparrot-clean": ("codeparrot/codeparrot-clean", "json.gz shards",
        "The Stack license", "file-*.json.gz",
        "~13GB gz real Python code content"),
    "hf_commitpackft": ("bigcode/commitpackft", "parquet/json",
        "permissive", "per-language files",
        "commit messages + diffs at scale — fix-pattern ore"),
    "hf_code_search_net": ("code-search-net/code_search_net", "json",
        "research", "per-language function records",
        "2M+ functions with docstrings across 6 languages"),
    "hf_pile": ("EleutherAI/pile", "jsonl.zst shards",
        "various", "pile-*.jsonl.zst",
        "~800GB general corpus incl code subset — longest download"),
}

def dir_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""CREATE TABLE datasets(
        id INTEGER PRIMARY KEY, name TEXT UNIQUE, source TEXT, format TEXT,
        license TEXT, local_path TEXT, size_bytes INTEGER,
        status TEXT, query_hint TEXT, notes TEXT, added_at TEXT DEFAULT (datetime('now')))""")
    cur.execute("""CREATE TABLE artifacts(
        id INTEGER PRIMARY KEY, dataset_id INTEGER REFERENCES datasets(id),
        kind TEXT, path TEXT, description TEXT)""")
    cur.execute("""CREATE TABLE claims_checked(
        id INTEGER PRIMARY KEY, ts TEXT DEFAULT (datetime('now')),
        agent TEXT, claim TEXT, dataset TEXT, query TEXT,
        result_summary TEXT, verified INTEGER)""")
    cur.execute("CREATE INDEX idx_artifacts_ds ON artifacts(dataset_id)")

    for name, (source, fmt, lic, hint, notes) in MANIFEST.items():
        path = os.path.join(DATASETS_DIR, name)
        if name == "runbugrun.sql.lrz":
            path = os.path.join(DATASETS_DIR, "runbugrun.sql.lrz")
        exists = os.path.exists(path)
        size = dir_size(path) if os.path.isdir(path) else (os.path.getsize(path) if exists else 0)
        status = "present" if exists and size > 0 else ("partial" if exists else "missing")
        cur.execute("""INSERT INTO datasets(name,source,format,license,local_path,
            size_bytes,status,query_hint,notes) VALUES(?,?,?,?,?,?,?,?,?)""",
            (name, source, fmt, lic, path, size, status, hint, notes))
        ds_id = cur.lastrowid
        if os.path.isdir(path):
            # record top-level artifacts
            try:
                for entry in sorted(os.listdir(path))[:50]:
                    ep = os.path.join(path, entry)
                    kind = "dir" if os.path.isdir(ep) else "file"
                    cur.execute("INSERT INTO artifacts(dataset_id,kind,path,description) VALUES(?,?,?,?)",
                                (ds_id, kind, entry, ""))
            except OSError:
                pass
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    print(f"catalog.db built: {n} datasets")
    for row in cur.execute("SELECT name,status,printf('%.1f GB',size_bytes/1e9) FROM datasets ORDER BY size_bytes DESC LIMIT 10"):
        print(" ", row)
    con.close()

if __name__ == "__main__":
    main()
