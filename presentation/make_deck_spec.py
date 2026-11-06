#!/usr/bin/env python3
"""Validate the current authored deck spec. Historical regeneration is separate."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent/'deck_spec.json';s=json.loads(p.read_text())
assert len(s['slides'])==13 and sum(x['duration_seconds'] for x in s['slides'])==300
assert sum(len(x['speaker_notes'].split()) for x in s['slides'])==s['spoken_script_whitespace_words']
print('Current status-aware spec retained: 13 slides, 300 planned seconds.')
