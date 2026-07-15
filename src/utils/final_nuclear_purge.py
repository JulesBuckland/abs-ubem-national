import os
import re

def final_nuclear_purge():
    # 1. Fix the mangled words caused by previous bad $T^*$ replacement
    # We replace '$T^*$' (literally) back with 'eti' when it is embedded in a word.
    # Note: re.sub uses backslashes for special characters.
    mangle_pattern = re.compile(r'([a-zA-Z])\$T\^\*([a-zA-Z])')
    
    # 2. Banned terms with word boundaries
    clean_patterns = {
        r'\bmicrosimulation\b': 'stock estimation',
        r'\bIPF\b': 'stratified expansion',
        r'\bDeterministic IMD-Stratified Expansion\b': 'Deterministic IMD-Stratified Expansion',
        r'\bThe Age-Built-Form Paradox\b': 'Age-Built-Form Paradox',
        r'\bETI\b': r'$T^*$'
    }
    
    # Case-insensitive versions for some
    clean_patterns_ci = {
        r'\bFabric-Vulnerability Paradox\b': 'Age-Built-Form Paradox',
        r'\bmicrosimulations\b': 'stock estimations'
    }

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
        'PROJECT_HANDOVER_FINAL.md',
        'README_LINKS.md'
    ]
    
    for f in files:
        if not os.path.exists(f):
            print(f"File not found: {f}")
            continue
            
        print(f"Purging: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # First, heal the mangled words
            # We do it iteratively to catch all
            while mangle_pattern.search(content):
                content = mangle_pattern.sub(r'\1eti\2', content)
            
            # Heal the specific \mak$T^*tle
            content = content.replace(r'\mak$T^*tle', r'\maketitle')
            
            # Now apply clean purges with word boundaries
            for p, r in clean_patterns.items():
                content = re.sub(p, r, content) # Case sensitive for $T^*$/stratified expansion
                
            for p, r in clean_patterns_ci.items():
                content = re.sub(p, r, content, flags=re.I)
                
            # Specifically fix headers and captions that were missed
            # (Adding a catch-all for the ones identified in audit)
            content = re.sub(r'Spatial stock estimation', 'Spatial stock estimation', content, flags=re.I)
            content = re.sub(r'Extending Spatial Stock Estimation', 'Extending Stock Estimation', content, flags=re.I)
            content = re.sub(r'stratified expansion Synthesis', 'Stratified Expansion', content)
            content = re.sub(r'Age-Built-Form Paradox', 'Age-Built-Form Paradox', content)
            
            # Fix Section 1 scope residual (just in case)
            content = re.sub(r'national housing stock of England and Wales', 'national housing stock of England', content)

            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Successfully purified: {f}")
        except Exception as e:
            print(f"Error purging {f}: {e}")

if __name__ == "__main__":
    final_nuclear_purge()
