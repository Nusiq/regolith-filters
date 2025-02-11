'''
This script is used for testing System Template that exports a file to the
'data' directory.

It tests the "data_export" system.
'''
from pathlib import Path

def main():
    path = Path("data/check_data/custom_data_file.txt")
    print(f"Testing if the custom data file exists: {path}")

    if not path.exists():
        raise Exception(f"Custom data file does not exist: {path}")

    print("Reading and printing the contents of the custom data file:")
    print(path.read_text())

if __name__ == "__main__":
    main()
