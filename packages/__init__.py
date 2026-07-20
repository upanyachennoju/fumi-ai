import sys
from pathlib import Path

# Add project root to sys.path to allow importing subpackages
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

