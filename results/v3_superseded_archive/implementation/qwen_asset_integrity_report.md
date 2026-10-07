# Qwen asset integrity report

Generated 2026-09-16T16:10:53Z.

- repository `Qwen/Qwen2.5-1.5B`, revision `8faed761d45a263340a0528343f099c05c9a4323`
- license Apache-2.0, not gated
- snapshot `/gpfs1/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/snapshots/8faed761d45a263340a0528343f099c05c9a4323`
- 7 files, **3,098,955,511 bytes** (expected 3,098,955,511 — match)
| file | bytes | sha256 |
|---|---|---|
| config.json | 684 | `0e8c8aa86468aba09c9d32157ff4bc2301c7e6c50e4398960425b2ea71e66f77` |
| generation_config.json | 138 | `8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8` |
| merges.txt | 1,671,839 | `599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3` |
| model.safetensors | 3,087,467,144 | `a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796` |
| tokenizer.json | 7,031,645 | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
| tokenizer_config.json | 7,228 | `c91efca15ceff6e9ee9424db58a6f59cd41294e550a86cbd07e3c1fb500b34f9` |
| vocab.json | 2,776,833 | `ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910` |

## Cross-validation

The `model.safetensors` blob filename is `a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796`, identical to its measured SHA-256. HF names LFS blobs by digest, so the 3 GB weight file is independently confirmed.

## Cache quirk that caused D5

The snapshot directory holds only symlinks into `../../blobs`, and the cache's `refs/` directory is **empty** because the download pinned an explicit revision. A repository-id lookup therefore cannot resolve the snapshot offline, which is exactly why loading must use the absolute snapshot path.
