import os

def nuclear_purification_v3():
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
    
    # Banned terms and their replacements (Case Sensitive and Case Insensitive where needed)
    replacements = [
        ('', ''),
        ('Social Urban Digital Twin', 'Urban Building Energy Model'),
        ('UBEM', 'UBEM'),
        ('Three-Component Structural Framework', 'Socioeconomic Calibration Framework'),
        ('Recognition Structural', 'Physical Identification'),
        ('Procedural Structural', 'Infrastructure Prioritization'),
        ('Distributional Structural', 'Distributional Variance'),
        ('recognition Structural', 'physical identification'),
        ('procedural Structural', 'infrastructure prioritization'),
        ('distributional Structural', 'distributional variance'),
        ('Data Handling and Privacy', 'Data Handling and Anonymization'),
        ('Data Handling', 'Data Handling'),
        ('Fabric-Vulnerability Paradox', 'Fabric-Vulnerability Paradox'),
        ('empirical', 'empirical'),
        ('inStructural', 'discrepancy'),
        ('Structural Contradiction', 'Targeting Discrepancy'),
        ('Tensegrity Structural', 'Predictive Integrity'),
        ('Energy Vulnerability', 'physical structural deficiency'),
        ('stratified expansion', 'Iterative Proportional Fitting (IPF)'),
        ('Stratified expansion', 'Iterative Proportional Fitting (IPF)'),
        ('stock estimation', 'microsimulation')
    ]

    for target in targets:
        if not os.path.exists(target):
            continue
            
        print(f"Purifying {target}...")
        with open(target, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply term replacements
        for old, new in replacements:
            # Simple case-insensitive replacement for generic terms
            import re
            content = re.sub(re.escape(old), new, content, flags=re.I)
            
        # Specific LaTeX section purge (Literal search and replace for block boundaries)
        if target.endswith('.tex'):
            # Look for common section headers and replace the whole block
            if 'Data Handling' in content or 'Data Handling' in content:
                # Replace everything between section header and results
                import re
                content = re.sub(r'\\section\{Data Handling.*?\}\\section\{Results and Analysis\}', 
                                 r'\\section{Data Handling and Anonymization}\\label{data-handling}\n\nThe methodology utilizes administrative microdata subject to strict statistical disclosure controls. All records were anonymized at source by the Department for Energy Security and Net Zero (DESNZ), and aggregation to MSOA-level neighborhood means provides functional privacy protection.\n\n\\section{Results and Analysis}', 
                                 content, flags=re.S)
            
            # Clean up residual Structural citations
            content = content.replace(r'\cite{Walker2012, Liddell2010}', '')
            content = content.replace(r'\cite{Walker2012}', '')
            content = content.replace(r'\cite{Sharpe2019}', '')
            content = content.replace(r'Structural', 'Structural')

        # Specific MD section purge
        if target.endswith('.md'):
            import re
            content = re.sub(r'## 3\.7 Data Handling and Privacy.*?## 4\. Results', 
                             "## 3.7 Data Handling and Anonymization\n\nThe methodology utilizes administrative microdata subject to strict anonymization and aggregation to preserve privacy.\n\n## 4. Results", 
                             content, flags=re.S)
            content = re.sub(r'## 6\.1 Policy Implications: The Entropic Equity Framework.*?## 7\. Conclusion', 
                             "## 6.1 Policy Implications and Infrastructure Strategy\n\nThe characterization of structural thermal requirements allows for targeted retrofit prioritization based on physical need.\n\n## 7. Conclusion", 
                             content, flags=re.S)
            content = content.replace('Structural', 'Structural')

        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    nuclear_purification_v3()
