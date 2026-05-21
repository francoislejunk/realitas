# Realitas Neo DATA-ONLY Backup Script
# Creates a lightweight zip with only simulation data (no code)
# Use this for sharing saves with others who already have the codebase

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$sourcePath = $PSScriptRoot
$backupName = "Realitas_Neo_DATA_$timestamp.zip"
$backupPath = Join-Path $env:USERPROFILE "Desktop\$backupName"
$tempDir = Join-Path $env:TEMP "realitas_backup_$timestamp"

Write-Host "=== Realitas Neo DATA Backup ===" -ForegroundColor Cyan
Write-Host "This creates a LIGHTWEIGHT backup (data only, no code)" -ForegroundColor Gray
Write-Host ""

try {
    # Create temp directory
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    # Copy essential data folders
    $dataFolders = @(
        "simulation_data",
        "WORLD_BUILDER"
    )
    
    $essentialFiles = @(
        ".env"
    )
    
    foreach ($folder in $dataFolders) {
        $src = Join-Path $sourcePath $folder
        if (Test-Path $src) {
            Write-Host "Copying $folder..." -ForegroundColor Yellow
            Copy-Item -Path $src -Destination $tempDir -Recurse -Force
        }
    }
    
    foreach ($file in $essentialFiles) {
        $src = Join-Path $sourcePath $file
        if (Test-Path $src) {
            Write-Host "Copying $file..." -ForegroundColor Yellow
            Copy-Item -Path $src -Destination $tempDir -Force
        }
    }
    
    # Create zip
    Write-Host "Creating zip archive..." -ForegroundColor Yellow
    Compress-Archive -Path "$tempDir\*" -DestinationPath $backupPath -Force -CompressionLevel Optimal
    
    # Cleanup temp
    Remove-Item -Path $tempDir -Recurse -Force
    
    $zipSize = (Get-Item $backupPath).Length / 1MB
    Write-Host ""
    Write-Host "SUCCESS! Data backup created:" -ForegroundColor Green
    Write-Host "  $backupPath" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Contains: simulation_data, WORLD_BUILDER, .env" -ForegroundColor Cyan
    Write-Host "To restore: Extract into existing Realitas Neo folder" -ForegroundColor Cyan
}
catch {
    Write-Host "ERROR: Failed to create backup" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force }
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
