import sys
from pathlib import Path

# The API is deployed with api/ as its working directory, so main.py imports
# its sibling modules by bare name. Mirror that for the tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
