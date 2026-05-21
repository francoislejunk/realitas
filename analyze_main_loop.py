"""Script to analyze and split main_loop.py into smaller chunks."""

import re

def analyze_main_loop():
    filepath = r'c:\Users\darre\OneDrive\Desktop\Realitas Neo\main_modules\main_loop.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    total_lines = len(lines)
    
    print(f"Total lines in main_loop.py: {total_lines}")
    
    # Find the main() function and its major sections
    # Look for patterns like major loops, initialization sections, etc.
    
    # Find lines that start major sections (comments that indicate sections)
    section_pattern = re.compile(r'^(\s*)#\s*(={3,}|[-]{3,})\s*(.+?)\s*(={3,}|[-]{3,})', re.IGNORECASE)
    header_pattern = re.compile(r'^(\s*)#\s*(SECTION|PHASE|PART|STAGE|SETUP|LOOP|INIT|MAIN|GAME|PLAY|INPUT|OUTPUT|RENDER|UPDATE|PROCESS|HANDLE|STEP)\s*[:\-]?\s*(.+)', re.IGNORECASE)
    
    sections = []
    
    for i, line in enumerate(lines, 1):
        # Check for section headers
        section_match = section_pattern.match(line)
        if section_match:
            indent = len(section_match.group(1))
            sections.append({
                'line': i,
                'indent': indent,
                'type': 'section',
                'title': section_match.group(3).strip()
            })
            continue
        
        header_match = header_pattern.match(line)
        if header_match:
            indent = len(header_match.group(1))
            sections.append({
                'line': i,
                'indent': indent,
                'type': 'header',
                'title': header_match.group(3).strip()
            })
    
    print(f"\nFound {len(sections)} potential section markers:")
    
    # Group by indentation level to understand hierarchy
    for i, sec in enumerate(sections[:50]):  # Show first 50
        prefix = "  " * (sec['indent'] // 4)
        print(f"  Line {sec['line']:5d}: {prefix}[{sec['type']}] {sec['title'][:60]}")
    
    if len(sections) > 50:
        print(f"  ... and {len(sections) - 50} more sections")
    
    # Also find while/for loops with large bodies
    loop_pattern = re.compile(r'^(\s*)(while|for)\s+')
    loops = []
    
    for i, line in enumerate(lines, 1):
        loop_match = loop_pattern.match(line)
        if loop_match:
            indent = len(loop_match.group(1))
            loops.append({'line': i, 'indent': indent, 'type': loop_match.group(2)})
    
    print(f"\nFound {len(loops)} loops")
    for loop in loops[:20]:
        print(f"  Line {loop['line']:5d}: {'  ' * (loop['indent'] // 4)}{loop['type']} loop")
    
    return sections, loops

if __name__ == '__main__':
    analyze_main_loop()
