Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$path = 'c:\Users\darre\OneDrive\Desktop\Realitas Neo\agents\decider_agent.py'
$content = Get-Content -Raw -LiteralPath $path

# Replace literal \r\n sequences with actual newlines
$content = $content -replace '\\r\\n', "`r`n"

# Normalize over-indented injected lines for determine_nua_reaction
$content = [regex]::Replace($content, '^(\s{9,})data = self\._call_llm_for_json\(prompt\.strip\(\)\)', '        data = self._call_llm_for_json(prompt.strip())', 'Multiline')
$content = [regex]::Replace($content, '^(\s{9,})# Return raw LLM JSON;.*$', '        # Return raw LLM JSON; Interpreter/Normalizer will validate/repair downstream', 'Multiline')
$content = [regex]::Replace($content, '^(\s{9,})return data or \{\}\s*$', '        return data or {}', 'Multiline')

# Normalize over-indented injected lines for determine_inua_reaction
$content = [regex]::Replace($content, '^(\s{9,})# Return raw LLM JSON;.*$', '        # Return raw LLM JSON; Interpreter/Normalizer will validate/repair downstream', 'Multiline')
$content = [regex]::Replace($content, '^(\s{9,})self\.logger\.log_system\(f"Successfully determined INUA reaction \(raw\) for \{reactor\.sheet\.name\}"\)\s*$', '        self.logger.log_system(f"Successfully determined INUA reaction (raw) for {reactor.sheet.name}")', 'Multiline')
$content = [regex]::Replace($content, '^(\s{9,})return response_data\s*$', '        return response_data', 'Multiline')

Set-Content -LiteralPath $path -Value $content -Encoding UTF8
Write-Output 'fix_decider_format: OK'
