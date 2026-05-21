"""Script to split redesigned_main.py into multiple files."""

import re
import os
import shutil
from pathlib import Path

def read_file(filepath):
    """Read entire file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    """Write content to file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_function_or_class(content, start_line, end_line=None):
    """Extract code block from start_line to end_line (1-indexed)."""
    lines = content.split('\n')
    start_idx = start_line - 1
    end_idx = end_line - 1 if end_line else len(lines)
    return '\n'.join(lines[start_idx:end_idx])

def find_all_definitions(content):
    """Find all class and function definitions with line numbers."""
    lines = content.split('\n')
    definitions = []
    
    for i, line in enumerate(lines, 1):
        # Class definition
        class_match = re.match(r'^class\s+(\w+)', line)
        if class_match:
            definitions.append({
                'type': 'class',
                'name': class_match.group(1),
                'line': i
            })
            continue
        
        # Function definition (top level - starts at column 0)
        func_match = re.match(r'^def\s+(\w+)', line)
        if func_match:
            definitions.append({
                'type': 'function',
                'name': func_match.group(1),
                'line': i
            })
    
    return definitions

def calculate_end_lines(content, definitions):
    """Calculate end line for each definition based on next definition."""
    total_lines = len(content.split('\n'))
    
    for i, defn in enumerate(definitions):
        if i + 1 < len(definitions):
            defn['end_line'] = definitions[i + 1]['line']
        else:
            defn['end_line'] = total_lines + 1
    
    return definitions

def group_definitions(definitions):
    """Group definitions by category based on naming patterns."""
    groups = {
        'mention_system': [],
        'narrative_context': [],
        'visualizer': [],
        'internal_voice': [],
        'ui_display': [],
        'spark_generation': [],
        'reputation_social': [],
        'dialogue': [],
        'location_travel': [],
        'main_loop': [],
        'misc': []
    }
    
    for d in definitions:
        name = d['name'].lower()
        
        if 'mention' in name:
            groups['mention_system'].append(d)
        elif any(x in name for x in ['visualizer', '_vis_', 'video', 'image']):
            groups['visualizer'].append(d)
        elif any(x in name for x in ['internal_voice', 'voice', 'perceptual']):
            groups['internal_voice'].append(d)
        elif any(x in name for x in ['display', '_box', 'render', 'ui_']):
            groups['ui_display'].append(d)
        elif any(x in name for x in ['spark', 'storyteller']):
            groups['spark_generation'].append(d)
        elif any(x in name for x in ['reputation', 'witness', 'stranger', 'sympathy', 'mood']):
            groups['reputation_social'].append(d)
        elif any(x in name for x in ['dialogue', 'fact', 'continuity', 'context']):
            groups['dialogue'].append(d)
        elif any(x in name for x in ['location', 'travel', 'destination', 'arrival']):
            groups['location_travel'].append(d)
        elif any(x in name for x in ['main', 'init', 'autostart']):
            groups['main_loop'].append(d)
        else:
            groups['misc'].append(d)
    
    return groups

def create_module_file(module_name, definitions, content, imports_header):
    """Create a module file with extracted definitions."""
    module_content = [imports_header]
    
    for d in definitions:
        code = extract_function_or_class(content, d['line'], d['end_line'])
        module_content.append(code)
        module_content.append('\n')
    
    filepath = f'c:/Users/darre/OneDrive/Desktop/Realitas Neo/main_modules/{module_name}.py'
    write_file(filepath, '\n'.join(module_content))
    print(f"Created: {filepath} ({len(definitions)} definitions)")

def main():
    main_file = r'c:\Users\darre\OneDrive\Desktop\Realitas Neo\MAIN\redesigned_main.py'
    content = read_file(main_file)
    
    # Find all definitions
    definitions = find_all_definitions(content)
    definitions = calculate_end_lines(content, definitions)
    
    print(f"Found {len(definitions)} definitions")
    print(f"Total lines: {len(content.split(chr(10)))}")
    
    # Group by category
    groups = group_definitions(definitions)
    
    # Show grouping summary
    print("\n=== GROUPING SUMMARY ===")
    for name, items in groups.items():
        if items:
            print(f"\n{name}: {len(items)} definitions")
            for item in items[:3]:
                print(f"  - {item['name']} (lines {item['line']}-{item['end_line']})")
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more")
    
    # Create imports header for modules
    imports_header = '''"""Auto-extracted from redesigned_main.py"""

import sys
import os
import time
import re
import json
import random
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# These imports will need to be adjusted based on what's actually used in each module
'''
    
    # Create modules
    print("\n=== CREATING MODULE FILES ===")
    for module_name, defs in groups.items():
        if defs:
            create_module_file(module_name, defs, content, imports_header)
    
    # Create main orchestrator stub
    orchestrator = '''"""Main orchestrator - imports from modules.

This is a slimmed-down version of redesigned_main.py that imports
from the main_modules package.
"""

# Import all the modules
from main_modules.mention_system import *
from main_modules.narrative_context import *
from main_modules.visualizer import *
from main_modules.internal_voice import *
from main_modules.ui_display import *
from main_modules.spark_generation import *
from main_modules.reputation_social import *
from main_modules.dialogue import *
from main_modules.location_travel import *
from main_modules.main_loop import *
from main_modules.misc import *

if __name__ == "__main__":
    main()
'''
    write_file('c:/Users/darre/OneDrive/Desktop/Realitas Neo/main_modules/orchestrator.py', orchestrator)
    print("\nCreated orchestrator.py")
    
    # Create __init__.py
    init_file = '''"""Main modules package - extracted from redesigned_main.py"""
'''
    write_file('c:/Users/darre/OneDrive/Desktop/Realitas Neo/main_modules/__init__.py', init_file)
    print("Created __init__.py")

if __name__ == '__main__':
    main()
