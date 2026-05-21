$scriptPath = 'c:\Users\darre\OneDrive\Desktop\Realitas Neo\MAIN\redesigned_main.py'
$workDir = 'c:\Users\darre\OneDrive\Desktop\Realitas Neo'
${env:PYTHONIOENCODING} = 'utf-8'
${env:PYTHONUTF8} = '1'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

# Inputs tailored to the session manager flow, then the friendly SPIRIT action, then quit
$inputs = @(
    '1',   # select first session in the menu
    'y',   # confirm resume if prompted
    'Offer a friendly fist bump to the nearest person with a smile.',
    'quit' # exit after first turn
)

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'python'
$psi.Arguments = "-u `"$scriptPath`""
$psi.WorkingDirectory = $workDir
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
$psi.EnvironmentVariables['PYTHONUTF8'] = '1'

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi
$null = $process.Start()

# Feed each line with small delays to match prompts
foreach ($line in $inputs) {
    $process.StandardInput.WriteLine($line)
    Start-Sleep -Milliseconds 600
}
$process.StandardInput.Close()

# Collect output
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()

# Persist logs to files to avoid console encoding issues
$logDir = Join-Path $workDir 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $logDir 'fist_bump_stdout.txt'), $stdout, $utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $logDir 'fist_bump_stderr.txt'), $stderr, $utf8NoBom)

Write-Host "Saved stdout to: $logDir\fist_bump_stdout.txt" -ForegroundColor Green
if ($stderr) { Write-Host "Saved stderr to: $logDir\fist_bump_stderr.txt" -ForegroundColor Yellow }

exit $process.ExitCode
