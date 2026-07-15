import os
import re

def absolute_heal_fixed():
    # Fix words mangled by PowerShell variable interpolation
    # Pattern is literally '^*' (superscript asterisk) inside words
    
    files = [
        'context.md',
        'data_architecture.md',
        'model_architecture_overview.md',
        'data_access_strategy.md',
        'manuscript/manuscript.md',
        'manuscript/COVER_LETTER.md',
        'session_history.md',
        'tasks/todo.md',
        'manuscript/manuscript.tex',
        'manuscript/supplementary_material.tex',
        'README_LINKS.md'
    ]
    
    for f in files:
        if not os.path.exists(f):
            continue
            
        print(f"Absolute Healing: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Heal cases where '^*' is inside or at the end of a word
            # Pattern: any letter + '^*' + any letter
            # We replace '^*' with 'eti'
            content = re.sub(r'([a-zA-Z])\^\*([a-zA-Z])', r'\1eti\2', content)
            
            # Heal cases where '$' was preserved but mangled (if any)
            content = re.sub(r'([a-zA-Z])\$T\^\*([a-zA-Z])', r'\1eti\2', content)
            
            # Specifically heal \mak^*tle
            content = content.replace(r'\mak^*tle', r'\maketitle')
            content = content.replace(r'\mak$T^*tle', r'\maketitle')
            
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    absolute_heal_fixed()
