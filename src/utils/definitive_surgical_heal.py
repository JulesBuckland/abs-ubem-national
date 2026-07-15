import os
import re

def definitive_surgical_heal():
    # Heal words mangled by PowerShell interpolation
    # Pattern: word + (optional $) + ^* + word
    
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
            
        print(f"Surgical Healing: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Heal embedded patterns: letter + (optional $) + ^ + * + letter
            # We replace the mangled sequence with 'eti'
            content = re.sub(r'([a-zA-Z])\$*\^\*([a-zA-Z])', r'\1eti\2', content)
            
            # Special case for the \mak$^*tle or \mak^*tle
            content = re.sub(r'\\mak\$*\^\*tle', r'\\maketitle', content)
            
            # Re-apply the $T^*$ -> $T^*$ purge correctly this time
            content = re.sub(r'\bETI\b', r'$T^*$', content)

            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    definitive_surgical_heal()
