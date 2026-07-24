import os
import re

def definitive_heal():
    # 1. Patterns to fix words mangled by PowerShell variable interpolation
    # Pattern is literally '^*' inside or at the end of a word.
    
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
            
        print(f"Definitive Healing: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Heal case-insensitive embedded '^*' (which was 'eti')
            # Example: theor^*cal -> theoretical
            content = re.sub(r'([a-zA-Z])\^\*([a-zA-Z])', r'\1eti\2', content)
            
            # Heal specific common mangles
            content = content.replace(r'\mak^*tle', r'\maketitle')
            content = content.replace(r'synth^*c', 'synthetic')
            content = content.replace(r'theor^*cal', 'theoretical')
            content = content.replace(r'arithm^*c', 'arithmetic')
            content = content.replace(r'targ^*ng', 'targeting')
            content = content.replace(r'parameterisa^*on', 'parameterisation')
            content = content.replace(r'aggrega^*on', 'aggregation')
            
            # Now, replace STANDALONE '^*' (which was '$T^*$') with '$T^*$'
            # We use \b to avoid matching internal ones (though handled above)
            # Standalone means surrounded by space or punctuation.
            content = re.sub(r'\B\^\*\B', r'$T^*$', content) # \B means not word boundary? No.
            # Actually, standalone '^*' might be ' ^* '.
            content = re.sub(r'(?<=[\s\(\[])\^\*(?=[\s\)\.\,\]])', r'$T^*$', content)
            
            # Re-apply the REAL $T^*$ -> $T^*$ purge correctly this time
            # Using \b to ensure no internal matches
            content = re.sub(r'\bETI\b', r'$T^*$', content)

            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    definitive_heal()
