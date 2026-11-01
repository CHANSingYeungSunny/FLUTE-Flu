# Poll the MIFlu chain until 40/40 verified (or a 4 h cap), printing progress.
$R = "/gpfs1/home/sychan552/stage5_a2_durable"
$sshArgs = @("-n","-o","BatchMode=yes","-o","IdentitiesOnly=yes","-i","$HOME\.ssh\id_ed25519","-o","PreferredAuthentications=publickey","cityu")
for ($i = 1; $i -le 48; $i++) {
  $n = & ssh @sshArgs "cd $R/code && /home/sychan552/.conda/envs/mlflu_hpc/bin/python miflu_controller_v2.py --count 2>/dev/null | tail -1"
  $q = & ssh @sshArgs "squeue -u sychan552 -h -o '%j %T'"
  $ts = Get-Date -Format "HH:mm:ss"
  Write-Output "[$ts] poll $i verified=$n queue=$($q -join ' / ')"
  if ([int]$n -ge 40) { Write-Output "ALL-40-VERIFIED"; exit 0 }
  $log = & ssh @sshArgs "tail -n 4 $R/code/miflu_a100_chain.log"
  Write-Output ($log -join "`n")
  Start-Sleep -Seconds 300
}
Write-Output "POLL-CAP-REACHED"
