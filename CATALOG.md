# Grace Corpus Catalog

| Dataset | Status | Size | Format | License | Query hint |
|---|---|---|---|---|---|
| BugsInPy | present | 3.2MB | repo | research | Bugs/ per-project bug dirs |
| CVEfixes | present | 8.7GB | zip (12.7GB) + repo | code MIT / data CC BY 4.0 | CVEfixes_v1.0.8.zip -> Code/ per-CVE dirs |
| Project_CodeNet | present | 0.0MB | tar.gz + extracted dirs | research use | metadata/*.csv per problem; data/<problem>/<lang>/s*.ext |
| Project_CodeNet.tar.gz | present | 8.3GB | tar.gz | research | extract to get full corpus |
| code_contests_hf | present | 7.6GB | parquet shards | DeepMind research | data/train-*.parquet, test-*.parquet |
| hf_ManySStuBs4J | present | 348.0MB | json/parquet | research | data files |
| hf_Multi-SWE-bench | present | 1.8GB | json/parquet | research | per-language instance dirs |
| hf_PrimeVul | present | 1.3GB | json/parquet | research | function-level records |
| hf_SWE-Gym | present | 43.6MB | parquet/json | MIT | data + trajectories |
| hf_SWE-bench | present | 120.1MB | parquet/json | MIT-ish research | data/{train,dev,test}-*.parquet |
| hf_SWE-bench_Multilingual | missing | 0.0MB | parquet | research | data/*.parquet |
| hf_SWE-bench_Verified | present | 2.1MB | parquet | research | data/*.parquet |
| hf_SWE-smith | present | 277.8MB | parquet | MIT | data/train-*.parquet |
| hf_bigvul | present | 253.0MB | json/parquet | research | function-level records |
| hf_bugswarm_ant | present | 0.0MB | json | research | records |
| hf_bugswarm_gradle | present | 0.0MB | json | research | records |
| hf_bugswarm_maven | present | 0.0MB | json | research | records |
| hf_bugswarm_python | present | 0.0MB | json | research | records |
| hf_code_search_net | present | 3.9GB | json | research | per-language function records |
| hf_codeparrot-clean | present | 12.8GB | json.gz shards | The Stack license | file-*.json.gz |
| hf_commitpackft | present | 1.6GB | parquet/json | permissive | per-language files |
| hf_devign | present | 80.1MB | json/parquet | research | function-level records |
| hf_pile | present | 0.0MB | jsonl.zst shards | various | pile-*.jsonl.zst |
| hf_the-stack-smol-xl | present | 9.6GB | json per lang | permissive-licensed subset | data/<lang>/data.json (has content!) |
| hf_the-stack-v2 | present | 108.8GB | parquet index | gated: HF account + license | data/<Lang>/train-*.parquet |
| libra-eval | present | 628.8MB | repo + JSONL datasets | Apache-2.0 | libra_eval/datasets/*.jsonl |
| run_bug_run | present | 0.2MB | repo + .lrz SQLite dump | research | restore: lrunzip runbugrun.sql.lrz; sqlite3 runbugrun.db |
| runbugrun.sql.lrz | present | 120.5MB | lrzip SQLite dump | research | lrunzip -z -> sqlite3 runbugrun.db |

## Jobs (in-flight downloads)

| Job | Status | Size | Expected | Note |
|---|---|---|---|---|
| code-contests-hf | GROWING | 7.6GB | 0GB | 41 parquet shards from HF |
| cvefixes-zip | GROWING | 8.7GB | 13GB | 64-part ranged download -> concat to CVEfixes_v1.0.8.zip |
| hf-batch-A | GROWING | 202.4GB | 0GB | download_hf.py: SWE-bench family, SWE-smith, Multi-SWE, SWE-Gym, ManySStuBs4J, bugswarm, devign, PrimeVul, bigvul |
| hf-batch-B | GROWING | 202.4GB | 0GB | download_content_sets.py: codeparrot-clean, commitpackft, code_search_net, pile |
| stack-smol-xl | GROWING | 9.6GB | 0GB | ungated Stack sample w/ content |
| stack-v2-index | DONE | 140.8GB | 141GB | snapshot_download 11 langs; DONE when ~141GB |
