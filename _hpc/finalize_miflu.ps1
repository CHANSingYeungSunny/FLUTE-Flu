# Finalise the MIFlu merge once all 40 cells are verified on the HPC.
# Run from the repo root:  pwsh -File _hpc/finalize_miflu.ps1
$ErrorActionPreference = "Stop"
$R = "/gpfs1/home/sychan552/stage5_a2_durable"
$ssh = @("-n","-o","BatchMode=yes","-o","IdentitiesOnly=yes","-i","$HOME\.ssh\id_ed25519","-o","PreferredAuthentications=publickey","cityu")

Write-Host "=== 1. fetch author_runs/L*_all7 from the HPC ==="
& ssh @ssh "tar -czf $R/author_runs/_all7_fetch.tgz -C $R/author_runs L24_all7 L36_all7 L48_all7 L60_all7"
if ($LASTEXITCODE -ne 0) { throw "remote tar failed" }
scp -o BatchMode=yes -o IdentitiesOnly=yes -i $HOME\.ssh\id_ed25519 -o PreferredAuthentications=publickey "cityu:$R/author_runs/_all7_fetch.tgz" _all7_fetch.tgz
if ($LASTEXITCODE -ne 0) { throw "scp failed" }
Write-Host ("tarball bytes = " + (Get-Item _all7_fetch.tgz).Length)
tar -xzf _all7_fetch.tgz -C author_runs
if ($LASTEXITCODE -ne 0) { throw "extract failed" }

$npz = (Get-ChildItem author_runs\L*_all7\pred_miflu_*.npz)
$man = (Get-ChildItem author_runs\L*_all7\manifest_miflu_*.json)
$res = (Get-ChildItem author_runs\L*_all7\results_miflu_*.csv)
$csv = (Get-ChildItem author_runs\L*_all7\predictions_miflu_*.csv)
Write-Host "npz=$($npz.Count) manifest=$($man.Count) results=$($res.Count) widecsv=$($csv.Count)"
if ($npz.Count -ne 40) { throw "expected 40 npz, got $($npz.Count)" }

Write-Host "=== 2. freeze the pre-merge table contract ==="
$base = Get-ChildItem paper_tables\BENCH_*.csv | Where-Object { $_.Name -notmatch 'post_evalwindow16|pre_evalwindow16|pre_miflu|_v100nlinear|_A100_DELTA' }
foreach ($f in $base) { Copy-Item $f.FullName "paper_tables\$($f.BaseName).post_evalwindow16_pre_miflu.csv" -Force }
Write-Host "frozen $((Get-ChildItem paper_tables\*.post_evalwindow16_pre_miflu.csv).Count) files"

Write-Host "=== 3. import the 40 cells into expanded_runs ==="
$seeds = 2021..2030
python scripts/import_miflu_predictions.py --npz-dir author_runs --horizons 24 36 48 60 --seeds @seeds 2>&1 | Select-Object -Last 12
$cellDirs = (Get-ChildItem hpc_results\expanded_runs\miflu_L*_s* -Directory)
Write-Host "imported cell dirs = $($cellDirs.Count)"

Write-Host "=== 4. fresh sacct dump + provenance ==="
& ssh @ssh "bash $R/code/_dump_sacct.sh"
scp -o BatchMode=yes -o IdentitiesOnly=yes -i $HOME\.ssh\id_ed25519 -o PreferredAuthentications=publickey "cityu:$R/code/_sacct_dump.csv" scripts\sacct_dump.csv
python scripts/build_bench_gpu_provenance.py 2>&1 | Select-Object -Last 10

Write-Host "=== 5. analysis chain ==="
python scripts/analysis_expanded.py 2>&1 | Select-Object -Last 12
python scripts/analysis_postprocess.py 2>&1 | Select-Object -Last 4
python scripts/seasonal_naive_baseline.py 2>&1 | Select-Object -Last 4
python scripts/plot_bench.py 2>&1 | Select-Object -Last 3
python scripts/plot_pareto.py 2>&1 | Select-Object -Last 3

Write-Host "=== 6. verify (row completeness will change: 64 -> 68 rows) ==="
python scripts/verify_bench_unchanged.py 2>&1 | Select-Object -Last 12
Write-Host "=== 7. MIFlu oracle ==="
python scripts/verify_miflu_oracle.py 2>&1 | Select-Object -Last 30
