# Realitas Neo Backup Script
# Creates a complete zip of the workspace including all simulation data

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$sourcePath = $PSScriptRoot
$backupName = "Realitas_Neo_Backup_$timestamp.zip"
$backupPath = Join-Path $env:USERPROFILE "Desktop\$backupName"

Write-Host "=== Realitas Neo Backup ===" -ForegroundColor Cyan
Write-Host "Source: $sourcePath" -ForegroundColor Gray
Write-Host "Destination: $backupPath" -ForegroundColor Gray
Write-Host ""

# Exclude .venv and __pycache__ to reduce size
$excludePatterns = @(
    ".venv",
    "__pycache__",
    "*.pyc",
    ".git"
)

Write-Host "Creating backup (this may take a moment)..." -ForegroundColor Yellow

try {
    # Use Compress-Archive with -Force to overwrite if exists
    Compress-Archive -Path "$sourcePath\*" -DestinationPath $backupPath -Force -CompressionLevel Optimal
    
    $zipSize = (Get-Item $backupPath).Length / 1MB
    Write-Host ""
    Write-Host "SUCCESS! Backup created:" -ForegroundColor Green
    Write-Host "  $backupPath" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Gray
    Write-Host ""
    Write-Host "This backup includes ALL simulation data (sessions, context, memories)." -ForegroundColor Cyan
}
catch {
    Write-Host "ERROR: Failed to create backup" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
