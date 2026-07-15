import os
import importlib.util
import sys

def check_imports(directory):
    failed = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                module_name = filepath.replace(directory, "").replace(os.sep, ".")[:-3]
                if module_name.startswith("."):
                    module_name = module_name[1:]
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, filepath)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    failed.append((filepath, str(e)))
    return failed

print("FAILS:", check_imports("C:/Users/jules/OneDrive - The University of Manchester/Internships/projects/energy/paper 5/src"))
