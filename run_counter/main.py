'''
This is just a stupid little tool that counts the number of runs in Regolith.
The output file is in .gitignore, so it won't be committed to the repo.
'''
from pathlib import Path

COUNTER_PATH = Path('data/run_counter/counter.txt')

def main():
    if not COUNTER_PATH.exists():
        COUNTER_PATH.parent.mkdir(parents=True, exist_ok=True)
        COUNTER_PATH.write_text('0')

    counter = int(COUNTER_PATH.read_text())
    counter += 1
    COUNTER_PATH.write_text(str(counter))

if __name__ == "__main__":
    main()