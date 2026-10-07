$ErrorActionPreference = 'Continue'
Set-Location 'c:\Users\Asus\Desktop\FYP code\MLFlu\recovery\author_repo'

Write-Output '=== ALL tracked files with git blob hash + size ==='
git --no-pager ls-tree -r -l HEAD

Write-Output ''
Write-Output '=== working tree python files present? ==='
Get-ChildItem -Recurse -File -Include *.py | ForEach-Object {
    $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    '{0}  {1}  {2}' -f $h.Substring(0,16), $_.Length, $_.FullName.Replace((Get-Location).Path + '\','')
}

Write-Output ''
Write-Output '=== dataset/illness file hashes (full sha256) ==='
Get-ChildItem 'dataset\illness' -File | ForEach-Object {
    $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    '{0}  {1,10}  {2}' -f $h, $_.Length, $_.Name
}

Write-Output ''
Write-Output '=== text_emb directory: count + sizes ==='
$te = Get-ChildItem 'dataset\illness\text_emb' -File
"count = $($te.Count)"
$te | Sort-Object Name | ForEach-Object { '  {0,10}  {1}' -f $_.Length, $_.Name }

Write-Output ''
Write-Output '=== repo top-level dirs ==='
Get-ChildItem -Directory | Select-Object -ExpandProperty Name