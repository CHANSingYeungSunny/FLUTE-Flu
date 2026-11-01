#!/bin/bash
# Determine, from upstream metadata only (light HTTP, no heavy python import),
# which transformers release first recognises model_type 'qwen3_5'.
echo '=== pypi: transformers latest + requires_python ==='
curl -s --max-time 40 https://pypi.org/pypi/transformers/json \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
info=d['info']
print('latest    :', info['version'])
print('requires_python:', info['requires_python'])
rels=sorted(d['releases'].keys())
print('n_releases:', len(rels))
print('last 15   :', rels[-15:])
"
echo
echo '=== github main: does src/transformers/models/qwen3_5 exist? ==='
curl -s --max-time 40 'https://api.github.com/repos/huggingface/transformers/contents/src/transformers/models?ref=main' \
  | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
except Exception as e:
    print('JSON parse failed:', e); raise SystemExit
if isinstance(d, dict):
    print('API error:', d.get('message')); raise SystemExit
names=[x['name'] for x in d]
q=[n for n in names if 'qwen' in n.lower()]
print('qwen model dirs on main:', q)
"
echo
echo '=== local cached config for Qwen3.8-27B-FP8 ==='
HC=/home/sychan552/scratch/hf_cache
find "$HC" -maxdepth 6 -name config.json -path '*Qwen3.8-27B-FP8*' 2>/dev/null | head -3
CFG=$(find "$HC" -maxdepth 6 -name config.json -path '*Qwen3.8-27B-FP8*' 2>/dev/null | head -1)
if [ -n "$CFG" ]; then
  echo "config: $CFG"
  python3 -c "
import json;d=json.load(open('$CFG'))
for k in ('model_type','architectures','hidden_size','num_hidden_layers','num_attention_heads','num_key_value_heads','dtype','torch_dtype','quantization_config','vocab_size','intermediate_size'):
    if k in d: print(f'{k}: {d[k]}')
print('all keys:', sorted(d.keys()))
"
else
  echo 'WARNING: config.json not found under the cache'
  ls -d /home/sychan552/scratch/hf_cache/* 2>/dev/null | head
fi
echo END
