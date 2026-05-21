"""
JSON Utilities for UTAS Simulation

Provides standardized JSON extraction and parsing functions that can handle
various response formats from different LLMs, including markdown-wrapped JSON,
extra text, and other common formatting issues.
"""

import json
import re
from typing import Optional, Dict, Any


def extract_and_parse_json(response_text: str) -> Optional[Any]:
    """
    Extracts and parses JSON from LLM response text that may contain extra formatting.
    
    Handles:
    - Pure JSON responses
    - JSON wrapped in markdown code blocks (```json ... ```)
    - JSON with extra text before/after
    - Multiple JSON objects (returns the first valid one)
    - Unescaped quotes in string values
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Parsed JSON dictionary, or None if no valid JSON found
    """
    if not response_text or not response_text.strip():
        return None
    
    response_text = response_text.strip()
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Capture fenced JSON (object or array)
    markdown_pattern = r'```(?:json)?\s*([\[{].*?[\]}])\s*```'
    markdown_matches = re.findall(markdown_pattern, response_text, re.DOTALL | re.IGNORECASE)
    
    for match in markdown_matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            fixed_json = _fix_json_formatting(match.strip())
            try:
                return json.loads(fixed_json)
            except json.JSONDecodeError:
                continue
    
    # Try to extract first top-level JSON object OR array by bracket balancing
    start_candidates = []
    obj_start = response_text.find('{')
    arr_start = response_text.find('[')
    if obj_start != -1:
        start_candidates.append((obj_start, '{'))
    if arr_start != -1:
        start_candidates.append((arr_start, '['))
    start_candidates.sort(key=lambda x: x[0])

    if start_candidates:
        json_start, start_char = start_candidates[0]
        open_char = start_char
        close_char = '}' if start_char == '{' else ']'
        depth = 0
        in_string = False
        escape = False
        json_end = None

        for i, ch in enumerate(response_text[json_start:], json_start):
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue

            if ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0:
                    json_end = i + 1
                    break

        if json_end is not None:
            json_string = response_text[json_start:json_end]
            try:
                return json.loads(json_string)
            except json.JSONDecodeError:
                fixed_json = _fix_json_formatting(json_string)
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError:
                    pass
    
    # Last resort: regex for a JSON object. (Arrays are too ambiguous for regex parsing.)
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, response_text, re.DOTALL)
    
    for match in json_matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            fixed_json = _fix_json_formatting(match.strip())
            try:
                return json.loads(fixed_json)
            except json.JSONDecodeError:
                continue
    
    return None


def _fix_json_formatting(json_string: str) -> str:
    """
    Fixes common JSON formatting issues that LLMs produce.
    
    Handles:
    - Unescaped quotes in string values (e.g., "Vincent "Vince" Russo")
    - Trailing commas
    - Newlines in the middle of JSON (malformed streaming responses)
    - Broken key names split across lines
    
    Args:
        json_string: Raw JSON string that may have formatting issues
        
    Returns:
        Fixed JSON string
    """
    import re
    
    # CRITICAL: Fix newlines breaking JSON keys/values
    # This handles cases like: {"needs":[],"
    #                          total_time_hours":0.0}
    # First, try to detect and fix broken JSON by removing problematic newlines
    # Look for patterns where a newline appears after a comma or colon inside JSON
    json_string = re.sub(r'",\s*\n\s*([a-zA-Z_])', r'", "\1', json_string)  # Fix broken keys after comma
    json_string = re.sub(r':\s*\n\s*(["\d\[\{])', r': \1', json_string)  # Fix broken values after colon
    
    # Also try collapsing all whitespace to single spaces and re-parsing
    # This is aggressive but handles many malformed cases
    collapsed = re.sub(r'\s+', ' ', json_string).strip()
    try:
        json.loads(collapsed)
        return collapsed  # If it parses, use the collapsed version
    except:
        pass  # Continue with line-by-line fixing
    
    # Fix unescaped quotes in string values by processing line by line
    lines = json_string.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Skip lines that don't contain key-value pairs
        if ':' not in line or '"' not in line:
            fixed_lines.append(line)
            continue
        
        # Find the colon that separates key from value
        colon_pos = line.find(':')
        if colon_pos == -1:
            fixed_lines.append(line)
            continue
        
        key_part = line[:colon_pos + 1]
        value_part = line[colon_pos + 1:].strip()
        
        # Check if this is a string value with potential unescaped quotes
        if value_part.startswith('"'):
            # Find where the string value ends (look for comma, closing brace, or end of line)
            # We need to be careful about nested structures
            quote_count = 0
            string_end = -1
            in_string = False
            
            for i, char in enumerate(value_part):
                if char == '"' and (i == 0 or value_part[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        quote_count += 1
                    else:
                        # This could be the end of the string or an unescaped quote
                        # Check if the next non-whitespace character is a comma, brace, or end
                        remaining = value_part[i+1:].lstrip()
                        if remaining == '' or remaining[0] in ',}]':
                            # This is the end of the string
                            string_end = i + 1
                            break
                        else:
                            # This is an unescaped quote inside the string
                            quote_count += 1
            
            if string_end > 0 and quote_count > 2:
                # Extract the string content and escape internal quotes
                string_content = value_part[1:string_end-1]  # Remove outer quotes
                escaped_content = string_content.replace('"', '\\"')
                remaining_part = value_part[string_end:]
                
                fixed_value = '"' + escaped_content + '"' + remaining_part
                fixed_lines.append(key_part + ' ' + fixed_value)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    fixed_string = '\n'.join(fixed_lines)
    
    # Remove trailing commas
    fixed_string = re.sub(r',(\s*[}\]])', r'\1', fixed_string)
    
    # Fix unterminated strings - if JSON ends mid-string, close it
    # Count quotes to detect unterminated strings
    quote_count = 0
    in_escape = False
    for char in fixed_string:
        if in_escape:
            in_escape = False
            continue
        if char == '\\':
            in_escape = True
            continue
        if char == '"':
            quote_count += 1
    
    # Odd number of quotes means unterminated string
    if quote_count % 2 == 1:
        # Try to close the string and complete the JSON
        fixed_string = fixed_string.rstrip()
        if not fixed_string.endswith('"'):
            fixed_string += '"'
        if not fixed_string.endswith('}'):
            # Check if we need to close braces
            open_braces = fixed_string.count('{') - fixed_string.count('}')
            open_brackets = fixed_string.count('[') - fixed_string.count(']')
            fixed_string += ']' * open_brackets + '}' * open_braces
    
    return fixed_string


def safe_json_extract(response_text: str, fallback_value: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Safely extracts JSON with a fallback value if extraction fails.
    
    Args:
        response_text: Raw response text from LLM
        fallback_value: Value to return if JSON extraction fails (default: empty dict)
        
    Returns:
        Parsed JSON dictionary or fallback value
    """
    result = extract_and_parse_json(response_text)
    if result is not None:
        return result
    
    return fallback_value if fallback_value is not None else {}
