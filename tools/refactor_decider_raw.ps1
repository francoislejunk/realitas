Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$path = 'c:\Users\darre\OneDrive\Desktop\Realitas Neo\agents\decider_agent.py'
$content = Get-Content -Raw -LiteralPath $path

# Remove ResponseNormalizer import if present
$content = $content -replace 'from response_normalizer import ResponseNormalizer(\r?\n)?',''

# Make determine_nua_reaction() return raw (remove normalization + enrichment)
$pattern1 = '(?s)data = self\._call_llm_for_json\(prompt\.strip\(\)\)\s*\r?\n\s*normalized_data = ResponseNormalizer\.normalize_reactor_response\([\s\S]*?\)\s*\r?\n\s*self\._enrich_utas_factors_with_actor_data\(normalized_data, reactor\)\s*\r?\n\s*return normalized_data'
$replacement1 = '        data = self._call_llm_for_json(prompt.strip())\r\n\r\n        # Return raw LLM JSON; Interpreter/Normalizer will validate/repair downstream\r\n        return data or {}'
$content = [regex]::Replace($content, $pattern1, $replacement1)

# Make determine_inua_reaction() return raw (remove normalization + enrichment)
$pattern2 = '(?s)normalized_data = ResponseNormalizer\.normalize_proactor_action_response\([\s\S]*?\)\s*\r?\n\s*if not normalized_data:\s*\r?\n\s*self\.logger\.log_system\(f"ERROR: Could not normalize INUA reaction for \{reactor\.sheet\.name\}"\)\s*\r?\n\s*return None\s*\r?\n\s*self\._enrich_utas_factors_with_actor_data\(normalized_data, reactor\)\s*\r?\n\s*self\.logger\.log_system\(f"Successfully determined INUA reaction for \{reactor\.sheet\.name\}"\)\s*\r?\n\s*return normalized_data'
$replacement2 = '        # Return raw LLM JSON; Interpreter/Normalizer will validate/repair downstream\r\n        self.logger.log_system(f"Successfully determined INUA reaction (raw) for {reactor.sheet.name}")\r\n        return response_data'
$content = [regex]::Replace($content, $pattern2, $replacement2)

Set-Content -LiteralPath $path -Value $content -Encoding UTF8
Write-Output 'refactor_decider_raw: OK'
