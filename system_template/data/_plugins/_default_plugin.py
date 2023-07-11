from pathlib import Path
import uuid
import math
import random

# Just in case one of the modules define reserved variables, we delete them
for forbidden_var in [
        "K", "JoinStr", "true", "false", "AUTO", "AUTO_SUBFOLDER",
        "AUTO_FLAT_SUBFOLDER","AUTO_FLAT"]:
    if forbidden_var in locals():
        del locals()[forbidden_var]
