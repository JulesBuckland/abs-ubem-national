import os
import sys

from src.inference.model_unified import run_national_unified_model

def main():
    print("==================================================")
    print("ABS-UBEM Production Runner (National Graph)")
    print("==================================================")
    run_national_unified_model()

if __name__ == "__main__":
    main()
