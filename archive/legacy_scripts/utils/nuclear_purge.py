import os
import re

def nuclear_purge():
    patterns = {
        r'stock estimation': 'stock estimation',
        r'stratified expansion': 'stratified expansion',
        r'Deterministic IMD-Stratified Expansion': 'Deterministic IMD-Stratified Expansion',
        r'Age-Built-Form Paradox': 'Age-Built-Form Paradox',
        r'$T^*$': r'$T^*$'
    }
    
    files = [
        'context.md',
        'data_architecture.md',
        'model_architecture_overview.md',
        'data_access_strategy.md',
        'manuscript/manuscript.md',
        'manuscript/COVER_LETTER.md',
        'session_history.md',
        'tasks/todo.md'
    ]
    
    for f in files:
        if not os.path.exists(f):
            print(f"File not found: {f}")
            continue
            
        print(f"Nuclear purge for {f}...")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            for p, r in patterns.items():
                content = re.sub(p, r, content, flags=re.I)
            
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Purged: {f}")
        except Exception as e:
            print(f"Error purging {f}: {e}")

if __name__ == "__main__":
    nuclear_purge()
