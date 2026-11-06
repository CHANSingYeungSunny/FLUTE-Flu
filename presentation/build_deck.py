#!/usr/bin/env python3
"""Build the current status deck while preserving the owner master package."""
from pathlib import Path
import argparse,json
from build_status_deck import build
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'Week12_Progress_Presentation.pptx');a=p.parse_args();print(json.dumps(build(a.out),indent=2))
