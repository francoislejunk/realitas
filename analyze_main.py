"""Script to analyze and split redesigned_main.py into manageable modules."""

import re
import os

# Read the main file in chunks
def read_file_chunks(filepath, chunk_size=50000):
    """Read file in chunks to avoid memory issues."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def extract_classes_and_functions(content):
    """Extract class and function definitions with their line numbers."""
    lines = content.split('\n')
    
    # Pattern for class definitions
    class_pattern = re.compile(r'^class\s+(\w+)')
    # Pattern for function definitions (top-level only)
    func_pattern = re.compile(r'^def\s+(\w+)')
    
    classes = []
    functions = []
    
    for i, line in enumerate(lines, 1):
        # Check for class
        class_match = class_pattern.match(line)
        if class_match:
            classes.append({
                'name': class_match.group(1),
                'line': i,
                'code': line
            })
        
        # Check for function (only at top level - no indent)
        func_match = func_pattern.match(line)
        if func_match:
            functions.append({
                'name': func_match.group(1),
                'line': i,
                'code': line
            })
    
    return classes, functions

def find_imports(content):
    """Find all import statements."""
    import_pattern = re.compile(r'^(import|from)\s+')
    lines = content.split('\n')
    imports = []
    for i, line in enumerate(lines, 1):
        if import_pattern.match(line):
            imports.append({'line': i, 'code': line})
    return imports

def main():
    filepath = r'c:\Users\darre\OneDrive\Desktop\Realitas Neo\MAIN\redesigned_main.py'
    
    print(f"Reading {filepath}...")
    content = read_file_chunks(filepath)
    
    total_lines = len(content.split('\n'))
    print(f"\nTotal lines: {total_lines}")
    
    # Extract imports
    imports = find_imports(content)
    print(f"\n=== IMPORTS (first 30) ===")
    for imp in imports[:30]:
        print(f"  Line {imp['line']}: {imp['code']}")
    
    # Extract classes and functions
    classes, functions = extract_classes_and_functions(content)
    
    print(f"\n=== CLASSES ({len(classes)} total) ===")
    for cls in classes:
        print(f"  Line {cls['line']}: {cls['name']}")
    
    print(f"\n=== FUNCTIONS ({len(functions)} total, first 50) ===")
    for func in functions[:50]:
        print(f"  Line {func['line']}: {func['name']}")
    
    # Group by category
    print("\n\n=== SUGGESTED MODULE STRUCTURE ===")
    
    # Analyze class names to suggest groupings
    mention_related = [c for c in classes if 'mention' in c['name'].lower()]
    narrative_related = [c for c in classes if any(x in c['name'].lower() for x in ['narrative', 'context', 'story'])]
    scene_related = [c for c in classes if any(x in c['name'].lower() for x in ['scene', 'spatial', 'location', 'map'])]
    ui_related = [c for c in classes if any(x in c['name'].lower() for x in ['ui', 'render', 'display', 'view', 'panel'])]
    agent_related = [c for c in classes if 'agent' in c['name'].lower()]
    
    print(f"\nMention System ({len(mention_related)} classes):")
    for c in mention_related:
        print(f"  - {c['name']} (line {c['line']})")
    
    print(f"\nNarrative/Context ({len(narrative_related)} classes):")
    for c in narrative_related:
        print(f"  - {c['name']} (line {c['line']})")
    
    print(f"\nScene/Spatial ({len(scene_related)} classes):")
    for c in scene_related:
        print(f"  - {c['name']} (line {c['line']})")
    
    print(f"\nUI/Display ({len(ui_related)} classes):")
    for c in ui_related:
        print(f"  - {c['name']} (line {c['line']})")
    
    print(f"\nAgents ({len(agent_related)} classes):")
    for c in agent_related[:20]:  # Limit output
        print(f"  - {c['name']} (line {c['line']})")

if __name__ == '__main__':
    main()
