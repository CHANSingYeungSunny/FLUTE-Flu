# Deploy & verify the innovation HPC bundle (Phase A)

Scientific protocol: `innov-v2.0` · implementation source:
`innov-v2.10`

| artefact | SHA-256 |
|---|---|
| archive `innovation_hpc_bundle.tar.gz` | `9b8c1516df1ce580c3ab6a70784e4c04c33faf0381243b4d7161ee02894029f1` |
| runtime file-set aggregate | `47a1404c8151539578d596f83742b2a7cc2d74607436a705a303e3c7d0d27fa4` |
| `hpc_scripts/hpc_env_check.sh` | `746bdf561ccab21f0e453e67d1949ce97cca9dbce2558ddb4ac7b7d8eb6b632c` |
| authoritative plan | `aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961` |

## 1. Upload (from the local repo root; adjust the remote path if needed)

```bash
scp results/innovation/hpc_deployment/innovation_hpc_bundle.tar.gz \
    results/innovation/hpc_deployment/innovation_hpc_bundle.tar.gz.sha256 \
    sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/
```

## 2. Extract into the ISOLATED deployment root on HPC

```bash
ssh sychan552@burgundy.hpc.cityu.edu.hk
cd /home/sychan552/scratch/CHATTIME
sha256sum -c innovation_hpc_bundle.tar.gz.sha256
mkdir -p /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.10_47a1404c
tar -xzf innovation_hpc_bundle.tar.gz -C /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.10_47a1404c
```

> **Never extract into the original reproduction repo** (`.../CHATTIME/Chattime`).
> The frozen innovation source lives in its own content-addressed isolated root, so
> the reproduction tree stays untouched and every deployment is independently
> verifiable. `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.10_47a1404c`

## 3. Authoritative deployment-root source verification (explicit root)

```bash
cd /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.10_47a1404c
export INNOVATION_DEPLOYMENT_ROOT="$PWD"
python scripts/innovation/verify_source_snapshot.py \
  --deployment-root "$INNOVATION_DEPLOYMENT_ROOT" \
  --manifest results/innovation/source_snapshot_manifest.json \
  --expect 47a1404c8151539578d596f83742b2a7cc2d74607436a705a303e3c7d0d27fa4
```
Exit code 0 and `actual_aggregate_sha256 == 47a1404c8151539578d596f83742b2a7cc2d74607436a705a303e3c7d0d27fa4` are REQUIRED.
A nested `results/innovation/source_snapshot` root is rejected with
`INVALID_NESTED_SNAPSHOT_ROOT`.

## 4. Environment facts (does NOT unlock pilot submission)

```bash
cd /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.10_47a1404c
INNOVATION_DEPLOYMENT_ROOT="$PWD" bash hpc_scripts/hpc_env_check.sh
```

## 5. Stop

Do **not** submit any pilot until the user explicitly authorizes it. The pilot
scripts additionally refuse to run unless `CONFIRM_INNOVATION_SUBMIT=YES`.
