import os
import re

def powershell_heal():
    # Fix words mangled by PowerShell swallowing '$T'
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
            
        print(f"PowerShell Healing: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Heal cases where '^*' is inside a word
            # Pattern 1: theor^*cal -> theoretical
            content = re.sub(r'theor\^\*cal', 'theoretical', content, flags=re.I)
            # Pattern 2: synth^*c -> synthetic
            content = re.sub(r'synth\^\*c', 'synthetic', content, flags=re.I)
            # Pattern 3: arithm^*c -> arithmetic
            content = re.sub(r'arithm\^\*c', 'arithmetic', content, flags=re.I)
            # Pattern 4: targ^*ng -> targeting
            content = re.sub(r'targ\^\*ng', 'targeting', content, flags=re.I)
            # Pattern 5: mak^*tle -> maketitle
            content = re.sub(r'mak\^\*tle', 'maketitle', content, flags=re.I)
            # Pattern 6: parameterisa^*on -> parameterisation
            content = re.sub(r'parameterisa\^\*on', 'parameterisation', content, flags=re.I)
            # Pattern 7: aggrega^*on -> aggregation
            content = re.sub(r'aggrega\^\*on', 'aggregation', content, flags=re.I)
            # Pattern 8: theor^*cs -> theoretics
            content = re.sub(r'theor\^\*cs', 'theoretics', content, flags=re.I)
            
            # General cleanup for any other word-embedded ones
            # letter + '^*' + letter
            content = re.sub(r'([a-zA-Z])\^\*([a-zA-Z])', r'\1eti\2', content)
            
            # Special case for '$T^*$' which became '^*'
            # We want to replace standalone '^*' with '$T^*$'
            # But only if it's NOT already in a word (handled above)
            # Actually, let's look for ' ^* ' or similar.
            content = re.sub(r'\b\^\*\b', r'$T^*$', content)
            
            # Re-apply the $T^*$ -> $T^*$ purge correctly this time
            content = re.sub(r'\bETI\b', r'$T^*$', content)

            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    powershell_heal()
