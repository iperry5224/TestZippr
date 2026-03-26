# Pushes this machine's TestZippr tree into a subfolder "TestZippr" on an existing GitHub repo.
# Usage:
#   cd C:\Users\iperr\TestZippr
#   .\push_TestZippr_to_github.ps1 -RepoUrl "https://github.com/OWNER/REPO.git"
#
# Requires: git, permission to push to the repo (HTTPS credential or SSH).

param(
    [Parameter(Mandatory = $true)]
    [string] $RepoUrl,
    [string] $SourceDir = $PSScriptRoot,
    [string] $SubfolderName = "TestZippr"
)

$ErrorActionPreference = "Stop"

$work = Join-Path ([System.IO.Path]::GetTempPath()) ("gh_TestZippr_" + [Guid]::NewGuid().ToString("n"))
New-Item -ItemType Directory -Path $work -Force | Out-Null
try {
    Set-Location $work
    Write-Host "Cloning $RepoUrl ..."
    git clone $RepoUrl repo
    $repoRoot = Join-Path $work "repo"
    Set-Location $repoRoot

    $dest = Join-Path $repoRoot $SubfolderName
    if (-not (Test-Path $dest)) {
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
    }

    Write-Host "Copying from $SourceDir to $dest (excluding security-venv) ..."
    robocopy $SourceDir $dest /E /XD "security-venv" ".git" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) {
        throw "robocopy failed with exit code $rc"
    }

    if (-not (Test-Path (Join-Path $dest ".gitignore"))) {
        Write-Warning ".gitignore not found under $dest — copy may be incomplete."
    }

    git add -- $SubfolderName
    $status = git status --porcelain
    if (-not $status) {
        Write-Host "Nothing new to commit (already in sync or all files ignored)."
        exit 0
    }

    git commit -m "Add/update $SubfolderName from local workspace"
    Write-Host "Pushing to origin ..."
    git push origin HEAD
    Write-Host "Done. Remote folder: $SubfolderName/"
}
finally {
    Set-Location $env:USERPROFILE
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
