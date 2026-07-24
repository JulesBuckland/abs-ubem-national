import os
import re

def absolute_heal():
    # Fix words mangled by bad '$T^*$' injection
    # Example: theor$T^*$cal -> theoretical
    
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
            
            # Heal cases where '$T^*$' is inside a word
            # Pattern: letter + '$T^*$' (literally) + letter
            # We replace it with 'eti'
            content = content.replace('$T^*$', 'eti')
            
            # Now we need to restore the legitimate $T^*$ symbols
            # These are the ones that were originally $T^*$ in caps and were alone
            # Or the ones in the math equations.
            
            # Re-apply the $T^*$ -> $T^*$ purge but only for full words
            content = re.sub(r'\bETI\b', r'$T^*$', content)
            
            # Restore the math environment for equations
            # My Eq 4 looks like: T^*_{m} = \exp ...
            # Wait, if I replaced all $T^*$ with 'eti', Eq 4 became T^*_{m} -> T^*_m? 
            # No, if it was T^*_{m}, the $T^*$ part was replaced by 'eti'.
            # So T^*_{m} -> eti_{m}. 
            # This is bad.
            
            # Better approach: Fix only the words that contain 'eti' and were mangled.
            # I will re-read the file and use a very specific regex.
            
            # [Re-reading file inside the loop]
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Pattern 1: theor$T^*$cal -> theoretical
            content = re.sub(r'theor\$T\^\*cal', 'theoretical', content, flags=re.I)
            # Pattern 2: synth$T^*$c -> synthetic
            content = re.sub(r'synth\$T\^\*c', 'synthetic', content, flags=re.I)
            # Pattern 3: arithm$T^*$c -> arithmetic
            content = re.sub(r'arithm\$T\^\*c', 'arithmetic', content, flags=re.I)
            # Pattern 4: targ$T^*$ng -> targeting
            content = re.sub(r'targ\$T\^\*ng', 'targeting', content, flags=re.I)
            # Pattern 5: mak$T^*$tle -> maketitle
            content = re.sub(r'mak\$T\^\*tle', 'maketitle', content, flags=re.I)
            # Pattern 6: parameterisa$T^*$on -> parameterisation
            content = re.sub(r'parameterisa\$T\^\*on', 'parameterisation', content, flags=re.I)
            # Pattern 7: aggrega$T^*$on -> aggregation
            content = re.sub(r'aggrega\$T\^\*on', 'aggregation', content, flags=re.I)
            # Pattern 8: theor$T^*$cs -> theoretics
            content = re.sub(r'theor\$T\^\*cs', 'theoretics', content, flags=re.I)
            
            # General cleanup for any other word-embedded ones
            content = re.sub(r'([a-zA-Z])\$T\^\*([a-zA-Z])', r'\1eti\2', content)
            
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    absolute_heal()
