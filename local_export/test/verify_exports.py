'''
Verifies that the files exported by the local_export filter during the
`regolith run` match the expected content. Run it from the test folder after
executing `regolith run`:

    python verify_exports.py
'''
import sys
from pathlib import Path

EXPECTED_FILES = [
    Path("expected_exports/exported_credits.md"),
    Path("expected_exports/exported_docs/source.md"),
]

failures = 0
for expected in EXPECTED_FILES:
    exported = Path(expected.name) if expected.parent == Path("expected_exports") \
        else Path("exported_docs") / expected.name
    try:
        exported_content = exported.read_bytes()
    except FileNotFoundError:
        print(f"FAIL: The exported file is missing: {exported}")
        failures += 1
        continue
    expected_content = expected.read_bytes()
    if exported_content == expected_content:
        print(f"OK: {exported} matches {expected}")
    else:
        print(f"FAIL: {exported} doesn't match {expected}")
        failures += 1

if failures > 0:
    sys.exit(1)
print("All exported files match the expectations.")
