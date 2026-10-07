$ErrorActionPreference = 'Continue'
Set-Location 'c:\Users\Asus\Desktop\FYP code\MLFlu\recovery\author_repo'

Write-Output '=== HEAD commit ==='
git --no-pager log -1 --format='COMMIT %H%nDATE %ci%nSUBJ %s'
Write-Output ''
Write-Output '=== remote -v ==='
git --no-pager remote -v
Write-Output ''
Write-Output '=== rev-parse HEAD / branch ==='
git --no-pager rev-parse HEAD
git --no-pager rev-parse --abbrev-ref HEAD
Write-Output ''
Write-Output '=== show-ref (all refs) ==='
git --no-pager show-ref
Write-Output ''
Write-Output '=== status --porcelain (working tree) ==='
git --no-pager status --porcelain
Write-Output ''
Write-Output '=== diff --stat HEAD ==='
git --no-pager diff --stat HEAD
Write-Output ''
Write-Output '=== git config (promisor/partial) ==='
git config --get remote.origin.promisor
git config --get remote.origin.partialclonefilter
git config --get remote.origin.url
Write-Output ''
Write-Output '=== reflog (when checked out) ==='
git --no-pager reflog --date=iso
Write-Output ''
Write-Output '=== log of origin/main ==='
git --no-pager log origin/main -1 --format='REMOTE_HEAD %H %ci %s'
Write-Output ''
Write-Output '=== tracked file list at HEAD ==='
git --no-pager ls-tree -r --name-only HEAD