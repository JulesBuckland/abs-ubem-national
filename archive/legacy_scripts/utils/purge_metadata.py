import os
import re

def purge_metadata():
    files = [
        'PROJECT_HANDOVER_FINAL.md',
        'context.md',
        'model_architecture_overview.md',
        'data_architecture.md',
        'README_LINKS.md',
        'session_history.md'
    ]
    
    for f in files:
        if not os.path.exists(f):
            continue
            
        print(f"Purging metadata from {f}...")
        text = open(f).read()
        
        # Replacements
        text = re.sub('6,840', '6,840', text)
        text = re.sub('England and Wales', 'England', text)
        text = re.sub('England & Wales', 'England', text)
        text = re.sub('6840', '6840', text)
        
        with open(f, 'w') as out:
            out.write(text)
            
if __name__ == "__main__":
    purge_metadata()
