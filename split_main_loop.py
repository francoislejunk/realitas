"""Split main_loop.py into smaller chunks based on sections."""

import re
import os

def split_main_loop():
    filepath = r'c:\Users\darre\OneDrive\Desktop\Realitas Neo\main_modules\main_loop.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    total_lines = len(lines)
    
    # Define split points based on major section headers found in analysis
    # Format: (line_number, module_name, description)
    split_points = [
        (1, 'main_init_start', 'Start of file'),
        (500, 'main_init_systems', 'System initialization'),
        (800, 'main_scene_setup', 'Scene setup and spatial context'),
        (1600, 'main_game_loop', 'Main game simulation loop'),
        (8000, 'main_input_handling', 'Input processing'),
        (10000, 'main_rendering', 'Rendering and display'),
        (12000, 'main_end', 'End sections'),
    ]
    
    # Create modules directory for main loop chunks
    chunks_dir = r'c:\Users\darre\OneDrive\Desktop\Realitas Neo\main_modules\main_loop_chunks'
    os.makedirs(chunks_dir, exist_ok=True)
    
    # Split the file
    for i in range(len(split_points) - 1):
        start_line = split_points[i][0]
        end_line = split_points[i + 1][0]
        module_name = split_points[i][1]
        description = split_points[i][2]
        
        # Extract lines (convert to 0-indexed)
        chunk_lines = lines[start_line - 1:end_line - 1]
        chunk_content = '\n'.join(chunk_lines)
        
        # Add header
        header = f'''"""{description}

Auto-extracted from main_loop.py (lines {start_line}-{end_line-1})
Original file: main_modules/main_loop.py
"""

'''
        
        chunk_file = os.path.join(chunks_dir, f'{module_name}.py')
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(header + chunk_content)
        
        line_count = len(chunk_lines)
        print(f"Created: {module_name}.py ({line_count} lines, {len(chunk_content)//1024} KB)")
    
    # Create __init__.py
    init_content = '''"""Main loop chunks - split from main_loop.py"""

# Import all chunks in order
from .main_init_start import *
from .main_init_systems import *
from .main_scene_setup import *
from .main_game_loop import *
from .main_input_handling import *
from .main_rendering import *
from .main_end import *
'''
    
    init_file = os.path.join(chunks_dir, '__init__.py')
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(init_content)
    
    print(f"\nCreated __init__.py in {chunks_dir}")
    print(f"\nSplit complete! main_loop.py is now in {len(split_points)-1} chunks.")

if __name__ == '__main__':
    split_main_loop()
