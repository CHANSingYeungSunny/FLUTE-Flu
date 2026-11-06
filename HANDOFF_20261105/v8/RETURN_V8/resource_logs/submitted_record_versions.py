#!/usr/bin/env python
# TASK 6 / t6_res - software version probe.
# This script runs INSIDE an sbatch compute-node job ONLY.
# AGENTS.md RULE 1: never run `import torch` on the Burgundy login node.
import sys
import platform
import json
import datetime

out = {}
out["utc"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
out["python_version"] = sys.version.replace("\n", " ")
out["python_executable"] = sys.executable
out["platform"] = platform.platform()

try:
    import numpy as np
    out["numpy"] = np.__version__
except Exception as e:
    out["numpy"] = "NOT_AVAILABLE: " + repr(e)

try:
    import pandas as pd
    out["pandas"] = pd.__version__
except Exception as e:
    out["pandas"] = "NOT_AVAILABLE: " + repr(e)

# `import torch` is permitted inside the sbatch compute-node job (AGENTS.md RULE 1).
try:
    import torch
    out["torch"] = torch.__version__
    out["torch_cuda_available"] = bool(torch.cuda.is_available())
    out["torch_cuda_device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
except Exception as e:
    out["torch"] = "NOT_AVAILABLE: " + repr(e)

print(json.dumps(out, indent=2, sort_keys=True))
