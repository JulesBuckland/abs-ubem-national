import pypandoc
import os

def generate_tex(md_file, tex_file, resource_path):
    if not os.path.exists(md_file):
        print(f"Error: {md_file} not found.")
        return
    
    extra_args = [
        '--citeproc', 
        '--bibliography=manuscript/bibliography.bib', 
        f'--resource-path={resource_path}'
    ]
    
    print(f"Converting {md_file} to {tex_file}...")
    try:
        pypandoc.convert_file(md_file, 'latex', outputfile=tex_file, extra_args=extra_args)
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    md_file = "manuscript/manuscript.md"
    tex_file = "manuscript/manuscript.tex"
    resource_path = "manuscript"
    generate_tex(md_file, tex_file, resource_path)
