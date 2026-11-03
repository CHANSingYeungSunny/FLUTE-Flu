# OUTAGE RECOVERY — what to run the *instant* the login node answers again

**What this is.** The exact, ordered recovery sequence for a CityU Burgundy login-node
outage, written because it was needed four times on 2026-11-01/02 and each time an agent
re-derived it from scratch. Kill the stuck probe **first**, before doing any science.

**When to read it.** The moment `ssh cityu` fails. Measure the signature, then follow the
matching branch below.

**What it points to.** `04_详细说明文档/HPC_RUNBOOK.md` gotcha 11 (D-state probes), gotcha 20 (the three
signatures), `04_详细说明文档/EXECUTION_PLAN_PART3.md` (what to resume afterwards).

---

## 0. MEASURE FIRST — the three signatures are not the same disease

Run this **before** drawing any conclusion (it needs no shell):

```powershell
Resolve-DnsName burgundy.hpc.cityu.edu.hk -Type A
Test-NetConnection -ComputerName burgundy.hpc.cityu.edu.hk -Port 22 -InformationLevel Quiet
```

| Result | Signature | Meaning | Remote remedy |
|---|---|---|---|
| DNS OK, **port 22 = False** | node down / isolated / firewalled | nothing reaches sshd | **none** — wait, retry, escalate after ~1 h |
| port 22 = True, auth OK, `exec request accepted`, then **zero bytes** | **gotcha 11** | login shell cannot spawn: leftover **D-state** `python -c "import transformers"` probes, parent `bash -c` wrappers running `du -sh` over conda/GPFS, or a hung GPFS mount | **yes, once a shell exists** — see §1 |
| `banner exchange: Connection to UNKNOWN port -1` | pre-auth banner never arrives | transitional / LB with no healthy backend | none |

**Measured 2026-11-02 04:20–04:35:** single A record `144.214.138.99`, **port 22 closed on
three consecutive probes 2 s apart**. That is branch 1 — *not* gotcha 11 — so the
"kill the D-state probe" remedy did **not** apply during that window: with the port closed
there is no shell, and a process cannot be signalled across hosts. Both agents that called it
"gotcha 11" were guessing from the ssh error string alone.

## 1. THE INSTANT A SHELL WORKS — kill the stuck probe before anything else

```bash
# 1. LOOK: what is stuck, and in what state?
ps -u $USER -o pid,stat,etime,cmd | head -30
#    'D' or 'D+' in STAT = uninterruptible sleep; these are the ones that wedge the node.

# 2. KILL the known culprits, most specific first
pkill -f 'import transformers'
pkill -f 'du -sh'
pkill -f dl_ds32.py
pkill -f 'python -c'

# 3. VERIFY they are gone (a D-state process ignores SIGKILL until its I/O completes,
#    so re-check; if one survives, it must finish or the sysadmin must intervene)
ps -u $USER -o pid,stat,etime,cmd | grep -E ' D| Z' | head

# 4. Only now check that the node is healthy for everyone
uptime; who | wc -l
```

**Why these three:** the 2026-11-01 post-mortem showed the outages were **not** the 66 GB
download (`hf_cache` was unchanged and no download process existed). They were two
`python -c "import transformers"` probes in state `D` for ~5 minutes plus their parent
`bash -c` wrappers running `du -sh` over the conda tree and `scratch` for up to 15 minutes.
A `D`-state process **ignores `kill -9`**, and while it holds the session the login shell
cannot be spawned — which is exactly the "auth OK, zero bytes" signature.

## 2. PREVENT THE NEXT ONE (the only durable fix)

| Never on the login node | Use instead |
|---|---|
| `python -c "import torch/transformers"` as a version probe | read a cached file, or `sbatch` a 1-minute job |
| `du -sh` over conda / `scratch` / `hpc_results` | `lfs quota` / one traversal at a time, never in parallel |
| any long-running or recursive command | wrap in `timeout 20s` |
| downloads | a `tiny`/`batch` job (both have internet via the proxy) |

## 3. WHEN ACCESS RETURNS — resume in this order

1. **Verify the driver is single.** `sacct -X -j 721031,721047` — only one may be `RUNNING`.
   Two drivers submit duplicate lanes; that is a self-inflicted collision.
2. **Verify the controller guard still carries both fixes.** `grep -c 'only a compute cell' master_controller_v2.sh`
   and confirm the competing-controller check is scoped to the stripe. Two agents patched the
   same function within four minutes of each other; one `os.replace` may have overwritten the other.
3. **Quarantine the 36 unseeded LLM cells** (`hpc_experiments/quarantine_unseeded_cells.py`,
   dry run first) — they are invalid because `manual_seed` was 42 for every seed.
4. **Merge the amended-protocol rows** (120 rows = 3 arms × 4 horizons × 10 seeds).
5. **Then** the queue work: Table VI (21 cells, ~1 A100-hour) → LLM arms → Table VIII →
   Table IX → rolling origin.
6. **Record the outage** in `04_详细说明文档/LEDGER.md` with the TCP result, so the next agent inherits
   the diagnosis rather than the error string.
