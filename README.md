# grace-corpus

The Grace dataset **catalog and verification gate**. The data itself lives
in `C:\Users\aaron\Desktop\datasets\` (too large for git); this repo shares
the *index of it* so Devin, AMP, and future agents can all answer
"does our corpus already contain X?" mechanically.

## Contents

- `corpus/catalog.db` — SQLite index: `datasets`, `artifacts`,
  `claims_checked` (audit log of every corpus verification run)
- `CATALOG.md` — human/agent-readable table of every dataset
- `tools/corpus_query.py` — the query gate:
  - `list` / `show <name>` / `search <text>` / `sql "<SELECT>"`
  - `check "<claim>" --dataset <name> --result "<summary>"` — logs a
    verification into `claims_checked`
- `tools/build_catalog.py` — rebuilds catalog.db by scanning the
  datasets folder (machine-specific paths; run on Aaron's PC)

## Doctrine

Before claiming prior art, a pattern, or a fix — query the catalog.
Every `check` call is logged, so corpus use is auditable. Catalog entries
describe *what exists and how to query it*; they are not evidence that a
claim is true — dataset contents still need verification per DOCTRINE.md.

## Regenerating

On the machine holding `Desktop\datasets`:

```
python tools/build_catalog.py
python - <<'EOF'   # refresh CATALOG.md from catalog.db
... (see git history / generate from datasets table)
EOF
```
