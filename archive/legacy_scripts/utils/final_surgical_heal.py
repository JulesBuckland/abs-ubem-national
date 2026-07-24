import os
import re

def final_surgical_heal():
    # Final cleanup of all mangled words
    # We identify any word-embedded '$T^*$' or '^*' and replace it with 'eti'
    
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
            
            # Heal case-insensitive embedded '$T^*$' (which was 'eti')
            # The pattern is: letter + (optional $) + T + ^ + * + letter
            # We use [ \$]*T\^\* to be safe
            content = re.sub(r'([a-zA-Z])[ \$]*T\^\*([a-zA-Z])', r'\1eti\2', content)
            
            # Heal specific common mangles that might be at start/end
            content = content.replace(r'\mak$T^*tle', r'\maketitle')
            content = content.replace(r'\mak^*tle', r'\maketitle')
            
            # Now, identify REAL $T^*$ instances (standalone words)
            # and replace them with $T^*$
            # We do this carefully
            content = re.sub(r'\bETI\b', r'$T^*$', content)
            
            # Final check for standalone '^*' or '$T^*' that are NOT in math mode
            # (though $T^*$ IS math mode in LaTeX)
            
            # Fix Equation 4 subscripts
            content = re.sub(r'T\$T\^\*\_\{m\}', r'T^*_m', content)
            content = re.sub(r'T\^\*\_\{m,h\}', r'T^*_m', content)

            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    final_surgical_heal()
