import re
from collections import defaultdict


def find_duplicates(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    defs = defaultdict(list)
    for i, line in enumerate(lines):
        match = re.search(r'^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(', line)
        if match:
            name = match.group(1)
            defs[name].append(i + 1)
    
    for name, line_nums in defs.items():
        if len(line_nums) > 1:
            print(f"Duplicate definition found: {name} at lines {line_nums}")

if __name__ == "__main__":
    find_duplicates("src/cogs/ora.py")
