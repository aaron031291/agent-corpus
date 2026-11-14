"""build_lookup.py — "where are we on X?" before building anything.

Event-driven existing-system check: given a feature/component/symbol,
report what the hub metadata ALREADY says — built / partial / missing —
across the status packet, plans, task board, journal, and knowledge docs.

Usage:
  python tools/build_lookup.py ledger
  python tools/build_lookup.py "self-learning" --repo "C:/Users/aaron/Desktop/Grace-Micro"

Verdict rules (honest, not optimistic):
  VERIFIED+wired in status packet  -> BUILT (do not rebuild; extend or reuse)
  state PARTIAL/UNPROVEN/BLOCKED   -> PARTIAL (find the gap before adding)
  name absent everywhere           -> NO RECORD (greenfield — but absence
                                      of record != absence of code; use
                                      --repo to check the actual source)
"""
import os, sys, json, re, glob

HUB = os.path.join(os.path.dirname(__file__), "..")
STATUS = os.path.join(HUB, "status", "grace-micro-status.json")


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def score(text, term):
    t, n = norm(term), norm(text)
    if not n:
        return 0
    if n == t:
        return 3
    if t in n or n in t:
        return 2
    # word-overlap for roles like "shared store lock"
    tw, nw = set(t.split()), set(n.split())
    if tw and len(tw & nw) / len(tw) >= 0.6:
        return 1
    return 0


def scan_components(term):
    hits = []
    if not os.path.exists(STATUS):
        return hits
    pkt = json.load(open(STATUS, encoding="utf-8"))
    comps = pkt.get("components", {})
    for name, c in comps.items():
        s = max(score(name, term), score(c.get("role", ""), term))
        if s:
            hits.append((s, name, c.get("state", "?"), c.get("wired"),
                         c.get("verified_at", ""), c.get("gaps") or []))
    return sorted(hits, key=lambda h: -h[0])


def scan_files(pattern_dir, term, extensions=("*.md",), limit_files=200):
    hits = []
    for fp in glob.glob(os.path.join(HUB, pattern_dir, "**", "*"), recursive=True):
        if not fp.lower().endswith(extensions):
            continue
        try:
            txt = open(fp, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        base = os.path.basename(fp)
        s = max(score(base, term), score(os.path.splitext(base)[0], term))
        mentions = len(re.findall(re.escape(term), txt, re.I))
        if s or mentions:
            hits.append((s + min(mentions, 5), fp, mentions, s))
    return sorted(hits, key=lambda h: -h[0])[:10]


def scan_repo(term, repo):
    """imports-level check: does the symbol/file exist in source?"""
    hits = []
    if not repo or not os.path.isdir(repo):
        return hits
    t = term.lower().replace(" ", "_").replace("-", "_")
    for dp, dn, fn in os.walk(repo):
        dn[:] = [d for d in dn if d not in (".git", "__pycache__", "node_modules", ".venv")]
        for f in fn:
            if f.lower() == t + ".py" or f.lower().startswith(t + "_") or f.lower().endswith("_" + t + ".py"):
                hits.append(os.path.join(dp, f))
        if len(hits) > 25:
            break
    return hits[:25]


def scan_git(term, repo, deep=False):
    """git log lookup: what was built, when, how — commit messages always,
    diff-content pickaxe only with deep=True (can be slow on big repos)."""
    import subprocess
    hits = {"msg": [], "diff": []}
    if not repo or not os.path.isdir(os.path.join(repo, ".git")):
        return hits
    def run(args, timeout=20):
        try:
            r = subprocess.run(["git", "-C", repo] + args,
                               capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip().splitlines() if r.returncode == 0 else []
        except Exception:
            return []
    hits["msg"] = run(["log", "--all", "--oneline", "-i",
                       f"--grep={term}", "-n", "15"])
    if deep:
        hits["diff"] = run(["log", "--all", "--oneline", "-G",
                            term.replace("-", "\\-"), "-n", "10",
                            "--", "*.py", "*.md"], timeout=40)
    return hits


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    term = " ".join(args) if args else ""
    repo = None
    if "--repo" in sys.argv:
        i = sys.argv.index("--repo")
        repo = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    if not term:
        sys.exit(__doc__)

    print(f"=== build_lookup: '{term}' ===\n")

    print("[1] STATUS PACKET (component truth)")
    comps = scan_components(term)
    if not comps:
        print("  no component name/role match")
    for s, name, state, wired, vat, gaps in comps:
        flag = "BUILT" if (state == "VERIFIED" and wired) else ("PARTIAL" if state != "MISSING" else "MISSING")
        print(f"  {flag:8s} {name:30s} state={state:10s} wired={wired} verified={vat}")
        for g in gaps[:3]:
            print(f"           gap: {g}")

    print("\n[2] PLANS (designs on record)")
    plans = scan_files("plans", term)
    if not plans:
        print("  no plan files matched")
    for s, fp, m, _ in plans:
        # status line from plan header
        status = ""
        try:
            head = open(fp, encoding="utf-8", errors="replace").read(600)
            mm = re.search(r"Status:\s*(\S+)", head)
            if mm:
                status = f" [{mm.group(1)}]"
        except OSError:
            pass
        print(f"  {os.path.basename(fp)}{status}  ({m} mentions)")

    print("\n[3] TASK BOARD + JOURNAL + KNOWLEDGE (activity record)")
    for label, pattern in (("tasks", "coordination/TASKS.md"),
                           ("journal", "journal"), ("knowledge", "knowledge")):
        hits = scan_files(pattern if pattern != "coordination/TASKS.md" else "coordination", term) \
            if pattern != "coordination/TASKS.md" else []
        if pattern == "coordination/TASKS.md":
            fp = os.path.join(HUB, pattern)
            if os.path.exists(fp):
                txt = open(fp, encoding="utf-8", errors="replace").read()
                lines = [l.strip() for l in txt.splitlines() if term.lower() in l.lower()]
                print(f"  TASKS.md: {len(lines)} matching lines")
                for l in lines[:5]:
                    print(f"    {l[:110]}")
            continue
        if hits:
            print(f"  {label}:")
            for s, fp, m, _ in hits[:5]:
                print(f"    {os.path.relpath(fp, HUB)} ({m} mentions)")

    deep = "--deep" in sys.argv
    repo = repo or r"C:\Users\aaron\Desktop\Grace-Micro"

    print("\n[4] REPO SOURCE (imports-level)")
    if repo:
        files = scan_repo(term, repo)
        if files:
            print(f"  {len(files)} file(s) name-match '{term}':")
            for f in files[:10]:
                print(f"    {f}")
            print("  NOTE: name-match is imports-level only — verify call path")
        else:
            print("  no filename match in repo")
    else:
        print("  (skipped — pass --repo <path> to check source too)")

    print("\n[5] GIT HISTORY (what/when/how was built)")
    gh = scan_git(term, HUB)
    rg = scan_git(term, repo, deep=deep) if repo and repo != HUB else {"msg": [], "diff": []}
    any_git = False
    if gh["msg"]:
        any_git = True
        print(f"  hub ({os.path.basename(HUB)}):")
        for l in gh["msg"][:8]:
            print(f"    {l[:100]}")
    if repo and repo != HUB:
        if rg["msg"]:
            any_git = True
            print(f"  repo ({repo}):")
            for l in rg["msg"][:8]:
                print(f"    {l[:100]}")
        if rg["diff"]:
            any_git = True
            print("  diff-mentions (--deep):")
            for l in rg["diff"][:8]:
                print(f"    {l[:100]}")
    if not any_git:
        print("  no commit-message matches — try --deep for diff-content search")

    print("\nVERDICT: see [1] for authoritative state. Name-match anywhere")
    print("else = weak signal; only status-packet state + repo call path = truth.")


if __name__ == "__main__":
    main()
