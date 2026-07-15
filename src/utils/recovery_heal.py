import os
import re

def recovery_heal():
    # Targeted recovery of mangled LaTeX commands and words
    
    files = [
        'manuscript/manuscript.tex',
        'manuscript/supplementary_material.tex'
    ]
    
    for f in files:
        if not os.path.exists(f):
            continue
            
        print(f"Recovery Healing: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Heal common mangled words
            content = re.sub(r'synth[a-zA-Z\$T\^\*]+c', 'synthetic', content, flags=re.I)
            content = re.sub(r'theor[a-zA-Z\$T\^\*]+cal', 'theoretical', content, flags=re.I)
            content = re.sub(r'arithm[a-zA-Z\$T\^\*]+c', 'arithmetic', content, flags=re.I)
            content = re.sub(r'targ[a-zA-Z\$T\^\*]+ng', 'targeting', content, flags=re.I)
            content = re.sub(r'\\mak[a-zA-Z\$T\^\*]+tle', r'\\maketitle', content, flags=re.I)
            
            # Heal the Delta elpd mess
            content = re.sub(r'Delta[a-zA-Z\$T\^\*]*elpd', r'Delta elpd', content, flags=re.I)
            
            # Heal the T* subscripts and math
            # TetiT^*_m or similar
            content = re.sub(r'T[a-zA-Z\$]*T\^\*', r'T^*', content)
            
            # Final sweep for any embedded '$T^*$' or '^*' in words
            # letter + sequence of [$, T, ^, *, space] + letter
            # We replace with 'eti'
            # (Re-running this but with more care)
            
            # Re-apply the England-only scope correctly
            content = re.sub(r'national housing stock of England and Wales', 'national housing stock of England', content)
            
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    recovery_heal()
