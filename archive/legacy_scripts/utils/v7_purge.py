import os
import re
import time

def global_purge():
    # Banned terms and their replacements
    replacements = [
        (re.compile(r'\bStructural\b', re.IGNORECASE), 'Structural'),
        (re.compile(r'\bUBEM\b', re.IGNORECASE), 'UBEM'),
        (re.compile(r'', re.IGNORECASE), ''),
        (re.compile(r'Fabric-Vulnerability Paradox', re.IGNORECASE), 'Fabric-Vulnerability Paradox'),
        (re.compile(r'Handling\b', re.IGNORECASE), 'Handling'),
        (re.compile(r'empirical', re.IGNORECASE), 'empirical')
    ]

    # Target directories
    dirs_to_purge = ['tasks', 'docs', 'scripts', 'manuscript']
    
    # Exclude files
    exclude_files = ['bibliography.bib']

    for d in dirs_to_purge:
        for root, dirs, files in os.walk(d):
            # Skip __pycache__ and archive if needed, but the prompt said "entire repository including tasks, docs, all scripts... excluding logs"
            # We will skip __pycache__ just to avoid breaking compiled files
            if '__pycache__' in root:
                continue
            
            for file in files:
                if file.endswith('.pyc') or file.endswith('.pdf') or file.endswith('.png') or file.endswith('.zip') or file in exclude_files:
                    continue
                
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    original_content = content
                    
                    for pattern, repl in replacements:
                        content = pattern.sub(repl, content)
                        
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Purged: {filepath}")
                except Exception as e:
                    # Ignore files that can't be read as utf-8
                    pass

if __name__ == "__main__":
    global_purge()
