import os
import re

def brute_force_heal():
    # Brute force heal of any mangled 'eti' residuals
    # The pattern is any combination of $, T, ^, * embedded between letters
    mangle_regex = re.compile(r'([a-zA-Z])[\$T\^\*]+([a-zA-Z])')
    
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
            
        print(f"Brute Force Healing: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Heal embedded mangles
            # We do it iteratively to catch overlapping or complex ones
            new_content = content
            while True:
                temp = mangle_regex.sub(r'\1eti\2', new_content)
                if temp == new_content:
                    break
                new_content = temp
            
            # Fix Equation 4 which is T^*_m
            # The regex above will turn T^*_m into Tetim
            # So we need to RESTORE Equation 4
            # We look for 'eti_m' or similar if they were mangled
            # Actually, Eq 4 is T^*_{m}
            # So T + ^ + * + _ + { + m
            # The regex above only hits letters.
            
            # Re-apply legitimate $T^*$ -> $T^*$ purge with word boundaries
            new_content = re.sub(r'\bETI\b', r'$T^*$', new_content)

            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Healed: {f}")
        except Exception as e:
            print(f"Error healing {f}: {e}")

if __name__ == "__main__":
    brute_force_heal()
