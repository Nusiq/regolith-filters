'''
This script is used to strip whitespace characters from the
mcfunction files. This simplifies testing the results of the subfunction filter
because the whitespaces are not important for mcfunction syntax so the changes
are inrelevant.
'''
from pathlib import Path

BP_PATH = Path('BP')

if __name__ == '__main__':
    for file in BP_PATH.rglob('*.mcfunction'):
        with file.open('r') as f:
            lines = f.readlines()

        with file.open('w') as f:
            stripped_lines = [ # List of all lines except empty ones
                l.strip() for l in lines if l.strip()]
            f.write('\n'.join(stripped_lines))

