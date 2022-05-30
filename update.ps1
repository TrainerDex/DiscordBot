Write-Host "Pulling the latest changes from the repository..."

Write-Host "Stashing any changes before pulling..."
git stash -u
if ($LASTEXITCODE -ne 0) {
    Write-Error "Stashing failed, aborting..."
    exit 1
}
else {
    Write-Verbose "Stashing successful, continuing..."
}

git fetch origin main:main && git checkout main
if ($LASTEXITCODE -ne 0) {
    Write-Error "Checkout failed, aborting..."
    exit 1
}
else {
    Write-Verbose "Checkout successful, continuing..."
}

Write-Information "Reloading docker..."
docker compose up -d --build --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Write-Error "Reloading docker failed, aborting..."
    exit 1
}
else {
    Write-Verbose "Reloading docker successful, continuing..."
}

$gitCommitHash = git rev-parse HEAD

Write-Host -ForegroundColor Green "Pull successful, commit hash: $gitCommitHash"