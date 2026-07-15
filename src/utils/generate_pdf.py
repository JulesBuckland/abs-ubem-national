import pypandoc
import os

def generate_pdf(md_path, pdf_path):
    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found.")
        return
    
    print(f"Converting {md_path} to {pdf_path}...")
    try:
        # We try to use pypandoc to generate the PDF directly
        # This requires pandoc and a PDF engine (like pdflatex) installed on the OS
        pypandoc.convert_file(md_path, 'pdf', outputfile=pdf_path)
        print("Success!")
    except Exception as e:
        print(f"Failed to generate PDF directly: {e}")
        print("Attempting to generate LaTeX first...")
        try:
            tex_path = md_path.replace('.md', '.tex')
            pypandoc.convert_file(md_path, 'latex', outputfile=tex_path)
            print(f"Generated LaTeX at {tex_path}. Please compile it manually if a PDF engine is missing.")
        except Exception as e2:
            print(f"Failed to generate LaTeX: {e2}")

if __name__ == "__main__":
    md_file = "manuscript/manuscript.md"
    pdf_file = "manuscript/manuscript.pdf"
    # Set resource path to the folder containing the figures
    resource_path = "manuscript"
    extra_args = [
        '--citeproc', 
        '--bibliography=manuscript/bibliography.bib', 
        '--pdf-engine=pdflatex',
        f'--resource-path={resource_path}'
    ]
    
    print(f"Converting {md_file} to {pdf_file}...")
    try:
        pypandoc.convert_file(md_file, 'pdf', outputfile=pdf_file, extra_args=extra_args)
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")
