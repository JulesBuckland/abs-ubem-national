import os
import re

def nuclear_purification():
    targets = [
        'manuscript/manuscript.tex',
        'manuscript/manuscript.md',
        'manuscript/cover_letter.md',
        'manuscript/manuscript_changelog.md',
        'context.md',
        'data_architecture.md',
        'docs/microsimulation_methodology.md',
        'model_architecture_overview.md'
    ]
    
    # Banned terms and their replacements
    replacements = {
        r'(?i)': '',
        r'(?i)Social Urban Digital Twin': 'Urban Building Energy Model',
        r'(?i)\bUBEM\b': 'UBEM',
        r'(?i)Three-Component Structural Framework': 'Socioeconomic Calibration Framework',
        r'(?i)Recognition Structural': 'Physical Identification',
        r'(?i)Procedural Structural': 'Infrastructure Prioritization',
        r'(?i)Distributional Structural': 'Distributional Variance',
        r'(?i)recognition Structural': 'physical identification',
        r'(?i)procedural Structural': 'infrastructure prioritization',
        r'(?i)distributional Structural': 'distributional variance',
        r'(?i)Data Handling': 'Data Handling',
        r'(?i)Fabric-Vulnerability Paradox': 'Fabric-Vulnerability Paradox',
        r'(?i)empirical': 'empirical',
        r'(?i)inStructural': 'discrepancy',
        r'(?i)Structural Contradiction': 'Targeting Discrepancy',
        r'(?i)Tensegrity Structural': 'Predictive Integrity',
        r'(?i)Energy Vulnerability': 'physical structural deficiency',
        r'(?i)stratified expansion': 'Iterative Proportional Fitting (IPF)',
        r'(?i)Stratified expansion': 'Iterative Proportional Fitting (IPF)',
        r'(?i)stock estimation': 'microsimulation'
    }

    # Specific block replacements
    # 1. Section 3.7 Data Handling and Privacy
    # LaTeX
    Handling_tex_regex = r'\\subsection\{Data Handling and Anonymization in National Scale Modeling\}\\label\{data-handling\}.*?\\section\{Results and Analysis\}'
    # Wait, the user said Section 3.7 was NOT removed. Let's look for the original title.
    Handling_tex_original = r'\\section\{Data Handling and Privacy in National Scale Modeling\}.*?\\section\{Results and Analysis\}'
    
    new_Handling_tex = r'\\section{Data Handling and Anonymization}\label{data-handling}\n\nThe methodology utilizes administrative microdata subject to strict statistical disclosure controls. All records were anonymized at source by the Department for Energy Security and Net Zero (DESNZ), and aggregation to MSOA-level neighborhood means provides functional privacy protection.\n\n\\section{Results and Analysis}'

    for target in targets:
        if not os.path.exists(target):
            continue
            
        print(f"Purifying {target}...")
        with open(target, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply term replacements
        for pattern, repl in replacements.items():
            content = re.sub(pattern, repl, content)
            
        # Specific LaTeX section purge
        if target.endswith('.tex'):
            content = re.sub(Handling_tex_original, new_Handling_tex, content, flags=re.S)
            content = re.sub(Handling_tex_regex, new_Handling_tex, content, flags=re.S)
            # Remove \cite{Walker2012}, \cite{Liddell2010} etc if they were associated with Structural
            content = content.replace(r'\cite{Walker2012, Liddell2010}', '')
            content = content.replace(r'\cite{Walker2012}', '')
            content = content.replace(r'\cite{Sharpe2019}', '')
            
        # Specific MD section purge
        if target.endswith('.md'):
            # Remove any residual Entropic Equity / Structural blocks
            content = re.sub(r'## 3\.7 Data Handling and Privacy.*?## 4\. Results', "## 3.7 Data Handling and Anonymization\n\nThe methodology utilizes administrative microdata subject to strict anonymization and aggregation to preserve privacy.\n\n## 4. Results", content, flags=re.S)
            content = re.sub(r'## 6\.1 Policy Implications: The Entropic Equity Framework.*?## 7\. Conclusion', "## 6.1 Policy Implications and Infrastructure Strategy\n\nThe characterization of structural thermal requirements allows for targeted retrofit prioritization based on physical need.\n\n## 7. Conclusion", content, flags=re.S)

        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    nuclear_purification()
