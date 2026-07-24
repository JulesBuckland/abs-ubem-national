import os
import re

def fix_mangled_words():
    # Fix words mangled by bad '$T^*$' injection
    # Example: theor$T^*$cal -> theoretical
    # Note: re.sub uses backslashes for special characters.
    
    # Mapping of mangled patterns to corrected substrings
    # The mangle was case-insensitive 'eti' -> '$T^*$'
    # So 'theoretical' -> 'theor$T^*$cal'
    
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
            
        print(f"Healing: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Heal cases where '$T^*$' is inside a word
            # Pattern: letter + '$T^*$' + letter
            # We replace '$T^*$' with 'eti'
            content = re.sub(r'([a-zA-Z])\$T\^\*([a-zA-Z])', r'\1eti\2', content)
            
            # Specifically heal \mak$T^*tle
            content = content.replace(r'\mak$T^*tle', r'\maketitle')
            
            # Heal cases where '$T^*$' is at the end of a word like 'synth$T^*' (if any)
            # Actually most are internal.
            
            # Fix residual 'theor^*cal' (where $ was missing in some logs?)
            content = re.sub(r'theor\^\*cal', 'theoretical', content)
            content = re.sub(r'synth\^\*c', 'synthetic', content)
            content = re.sub(r'arithm\^\*c', 'arithmetic', content)
            content = re.sub(r'targ\^\*ng', 'targeting', content)
            
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    fix_mangled_words()
