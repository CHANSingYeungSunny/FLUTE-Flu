#!/bin/bash
# Which transformers release first ships model_type 'qwen3_5', and what Python does
# each 5.x release require? Light HTTP only - no python imports of heavy libs.
echo '=== PyPI: 5.x releases and their requires_python ==='
curl -s --max-time 60 https://pypi.org/pypi/transformers/json | python3 -c "
import json,sys
d=json.load(sys.stdin)
rows=[]
for v,files in d['releases'].items():
    if not v.startswith('5.'):
        continue
    rp = files[0].get('requires_python') if files else None
    rows.append((tuple(int(x) for x in v.split('.') if x.isdigit()), v, rp))
rows.sort()
for _,v,rp in rows:
    print(f'{v:10s} requires_python={rp}')
print('total 5.x:', len(rows))
"
echo
echo '=== files inside src/transformers/models/qwen3_5 on main ==='
curl -s --max-time 40 'https://api.github.com/repos/huggingface/transformers/contents/src/transformers/models/qwen3_5?ref=main' \
 | python3 -c "
import json,sys
d=json.load(sys.stdin)
if isinstance(d,dict): print('ERR', d.get('message'))
else: print([x['name'] for x in d])
"
echo
echo '=== which 5.x tags actually contain the qwen3_5 directory? ==='
PROBE=configuration_qwen3_5.py
for v in 5.3.0 5.4.0 5.5.0 5.5.4 5.6.0 5.7.0 5.8.0 5.9.0 5.10.0 5.12.0 5.15.0 5.18.0 5.20.0 5.22.1; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 \
    "https://raw.githubusercontent.com/huggingface/transformers/v$v/src/transformers/models/qwen3_5/$PROBE")
  echo "v$v  $PROBE -> HTTP $code"
done
echo END
