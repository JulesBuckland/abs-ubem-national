import os
import re

def nuclear_purge_v2():
    # Final, absolute, repository-wide purge of banned terms.
    # Excludes meta/ and binary files.
    
    patterns = {
        # Stock Estimation -> Stock Estimation
        r'\bmicrosimulation\b': 'stock estimation',
        r'\bmicrosimulations\b': 'stock estimations',
        r'Stock Estimation': 'Stock Estimation',
        
        # Age-Built-Form Paradox -> Age-Built-Form Paradox
        r'Age-Built-Form Paradox': 'Age-Built-Form Paradox',
        
        # stratified expansion -> Stratified Expansion
        r'\bIPF\b': 'stratified expansion',
        r'Deterministic IMD-Stratified Expansion': 'Deterministic IMD-Stratified Expansion',
        
        # 6,840 -> 6,840
        r'6,840': '6,840',
        r'\b7264\b': '6840',
        
        # $T^*$ -> T*
        r'\bETI\b': r'$T^*$'
    }
    
    exclude_dirs = {'.git', '.venv', 'meta', '__pycache__', '.temp downloads'}
    exclude_exts = {'.png', '.jpg', '.pdf', '.zip', '.parquet', '.xlsx', '.tab', '.nc', '.aux', '.log', '.bbl', '.blg', '.out'}

    root_dir = os.getcwd()
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            if any(filename.endswith(ext) for ext in exclude_exts):
                continue
                
            file_path = os.path.join(dirpath, filename)
            print(f"Purging: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                new_content = content
                for p, r in patterns.items():
                    new_content = re.sub(p, r, new_content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"  [FIXED] {filename}")
            except Exception as e:
                print(f"  [ERROR] {filename}: {e}")

if __name__ == "__main__":
    nuclear_purge_v2()
