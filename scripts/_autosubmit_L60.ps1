# Auto-submit L=60 after L=48 (506643) finishes, to respect QOS 1-pending limit.
# Run in background; polls every 120s; submits L=60 once L=48 is gone from queue.
$ErrorActionPreference = 'Continue'
$log = "c:/Users/Asus/Desktop/FYP code/MLFlu/scripts/_autosubmit_L60.log"
$submitted = $false
$deadline = (Get-Date).AddHours(6)  # safety: give up after 6h

function Log($m) { "$((Get-Date) -f 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -Append $log }

Log "AUTOSUBMIT_L60 started; watching job 506643."
while (-not $submitted -and (Get-Date) -lt $deadline) {
    try {
        $out = ssh -o ConnectTimeout=20 sychan552@burgundy.hpc.cityu.edu.hk 'squeue -j 506643 2>&1'
    } catch {
        $out = "SSH_ERR"
    }
    if ($out -match 'Invalid job id|Not found|error') {
        Log "L=48 (506643) no longer in queue -> submitting L=60."
        try {
            $r = ssh -o ConnectTimeout=30 sychan552@burgundy.hpc.cityu.edu.hk 'cd /home/sychan552/scratch/CHATTIME/Chattime && MIFLU_HORIZON=60 sbatch submit_miflu_paper_protocol.sh 2>&1'
            Log "SUBMIT RESULT: $r"
            if ($r -match 'Submitted batch job (\d+)') {
                Log "L=60 submitted as job $($Matches[1]). DONE."
                $submitted = $true
            } else {
                Log "SUBMIT UNEXPECTED: $r"
            }
        } catch {
            Log "SUBMIT EXCEPTION: $_"
        }
    } else {
        Log "L=48 still running/pending. Sleeping 120s."
        Start-Sleep -Seconds 120
    }
}
if (-not $submitted) { Log "AUTOSUBMIT_L60 gave up after deadline or error." }
