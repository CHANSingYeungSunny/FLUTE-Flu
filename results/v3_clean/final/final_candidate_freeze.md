# Final Candidate Freeze — gpt2_miflu

Frozen from authorized Validation evidence only. No Test/Holdout, runtime, storage, PTE/PIE, partial-horizon, or subjective criterion was used.

- **Final candidate**: `gpt2_miflu` (family `llm`, arm `primary`)
- **Ranking metric**: `average_MSE_4L` (seven-variable, full-horizon, z-space, lower better)
- **Winner mean**: `0.7708721562796242`
- **Runner-up (Non-LLM)**: `nlinear` = `1.0697672040053035`
- **Paired t (winner vs runner)**: `-13.329`, p = `3.13e-07`

## Identities (hashes verified at freeze time)

- selection rule sha256: `afa7a780010aeed20fd7a2d361300ae2ce4411baeed1d458581538d3df359325`
- selection outcome sha256: `f93e711288023703b7c6ed7818009e7598c70f6dc9ed4c9274691ea16f667dc4`
- frozen analysis protocol sha256: `cd229790fd0693334d79a1d63a38f06be8faf8cf30d83eb45c70603bc580fb6f`

## Supporting accepted rows

- count: `40` (orders 161–200, seeds 42–51, horizons 24/36/48/60)

## Checkpoint identity (per run)

Each run carries an original training job_id (sacct) and the v3.15 compact_sha256 (authoritative content hash).

| run_key | job_id | compact_sha256 |
|---|---|---|
| `primary__gpt2_miflu__L24__seed42__w1` | 571231 | `acace30755848ea741da4102e3556c35aea31497568f17a9168ac80a634483ef` |
| `primary__gpt2_miflu__L24__seed43__w1` | 571234 | `12c8de46e8a1fd228ee7a158d6d40590b07279e16f3224eb2e9c2f4964242a96` |
| `primary__gpt2_miflu__L24__seed44__w1` | 571236 | `103567d61edb98caf3676b59803c92d9b2e40f18b7a225170be20b321373b140` |
| `primary__gpt2_miflu__L24__seed45__w1` | 571269 | `4ec7e03d8cdec578fd9634a68aa87fb1292a5a36c323896cb80e5e9753a9f333` |
| `primary__gpt2_miflu__L24__seed46__w1` | 571272 | `4ae3843c759df0022f33c86502a0615706857e321d0b8a45e29fe16d9cfa5c08` |
| `primary__gpt2_miflu__L24__seed47__w1` | 571275 | `35f34e83f070df8a4fc2455cbfd6be998fcdd3648d3270a145f0c4a6b741e8fa` |
| `primary__gpt2_miflu__L24__seed48__w1` | 571281 | `376afb2435e44a5c92a3a382d36090ffa249e90e6146da7b375b646ab2371f35` |
| `primary__gpt2_miflu__L24__seed49__w1` | 571284 | `003a8af6ab1ad6ca78fcb15e28f67e58ea76f7073dd5a0a85ff2fdd1ccac32c4` |
| `primary__gpt2_miflu__L24__seed50__w1` | 571289 | `462aaf1be7e91f117c93e5c122800a48f822d6f48499dc6d49161877df0dc7bd` |
| `primary__gpt2_miflu__L24__seed51__w1` | 571291 | `a000cb5aef3d5a1d722299ee4987145bc6d8ed962a4694ec4bd7ce006e5ece20` |
| `primary__gpt2_miflu__L36__seed42__w1` | 571294 | `b61128a3ad7ce6f57deeaabd883cbe0eb861658b1b820565ad816eb5b0163dd8` |
| `primary__gpt2_miflu__L36__seed43__w1` | 571308 | `5ed81ccb8d681ddcbda42b27996ab8522757a2651a23b51f5580ef010d70a89e` |
| `primary__gpt2_miflu__L36__seed44__w1` | 571315 | `770c3b150450b1898e57bd04dddb6063d2e29ad66d41ed61c8a515050696a1ef` |
| `primary__gpt2_miflu__L36__seed45__w1` | 571322 | `f5793f8bd1fc361b25f1128c2374aea14a2e5a7b29f94ef9ccf148f202e71f07` |
| `primary__gpt2_miflu__L36__seed46__w1` | 571330 | `54d476004a7db13ac6897470597aaf6b9bc7556f02538aac00bd0fa3413d3acd` |
| `primary__gpt2_miflu__L36__seed47__w1` | 571335 | `6549e46d58f99ac91e137babbb23997909666be915aac076bf4668c9cf21fc3c` |
| `primary__gpt2_miflu__L36__seed48__w1` | 571346 | `2cf386300faeda746e09e0df3cde588b68f8b62e4ebe7128853beb267fad6881` |
| `primary__gpt2_miflu__L36__seed49__w1` | 571349 | `35a67dc634128794b4c780b9915e163da296070e33f3b08f3bbe652e5eb4b768` |
| `primary__gpt2_miflu__L36__seed50__w1` | 571354 | `5d2f1ee47b5ebcb83f1ec50f4d5ae86e5adac8b18f4292266bc844fbddb1a1f2` |
| `primary__gpt2_miflu__L36__seed51__w1` | 571356 | `8bda77bc405c126e69dc8fbabb737b5283950ff9a33ea792a220c3a3284744bd` |
| `primary__gpt2_miflu__L48__seed42__w1` | 571359 | `5f326f7820ae0bbe37fb802192890b28805934cc7f66a92e62adb9ba1726d627` |
| `primary__gpt2_miflu__L48__seed43__w1` | 571362 | `c03b5c96f093b79e0840c95a5398af0412efa36504df9745d5197e04ade4cc0a` |
| `primary__gpt2_miflu__L48__seed44__w1` | 571364 | `e4104a9594e815260579904c9b49d2f576362067dbeeb6ff7f822af82ebddf9d` |
| `primary__gpt2_miflu__L48__seed45__w1` | 571371 | `65f18497732aabbfe080439fb0bd34fd7c230e1812499b8bb805a57bdf0b7506` |
| `primary__gpt2_miflu__L48__seed46__w1` | 571373 | `b8567c58e10870fc705d2e239cbc7e1d487e4c7f247622e81e6374a11b9fec94` |
| `primary__gpt2_miflu__L48__seed47__w1` | 571378 | `869d5cb81c4f0ea671077a0b1961a3b2c3bc3f5585aad6f853fa389616841b86` |
| `primary__gpt2_miflu__L48__seed48__w1` | 571383 | `ad958b40ffa24cca275a1978b783d5fbabe05f7a00524f1e5acfacb63b77c46d` |
| `primary__gpt2_miflu__L48__seed49__w1` | 571387 | `33c44cbd7cf702ac106e8f476f78c14a6e0c7df4148c4ce33687a1f07a481625` |
| `primary__gpt2_miflu__L48__seed50__w1` | 571393 | `b810afdf129565172478506bad6056716864daad6b1ad01f7c2e59369745b9fa` |
| `primary__gpt2_miflu__L48__seed51__w1` | 571396 | `0c6d6facd455e9f6ed5bc3d8235700019b0ea80ad769ee4557085f57246f1501` |
| `primary__gpt2_miflu__L60__seed42__w1` | 571398 | `cdfafa7c05eab68f52397713260a6b56ee1064aa4489070e8860419c21887fde` |
| `primary__gpt2_miflu__L60__seed43__w1` | 571401 | `581a4ca93fb09b9d69a492934846b25e26b70bc4b70c6ca3b16dfbae81ecae8f` |
| `primary__gpt2_miflu__L60__seed44__w1` | 571402 | `578334ddd9f838d7828de8b1e0f222002b775daedcb9b2a4b93fe9eff776a85b` |
| `primary__gpt2_miflu__L60__seed45__w1` | 571404 | `3924121749dfe59940894daa9edcbf2b13a2c65c335857786854b08d9453c1f0` |
| `primary__gpt2_miflu__L60__seed46__w1` | 571408 | `88ddc26c831dea361774dabd50efb9d4b69b74402b3b6c83d096e69770ee1353` |
| `primary__gpt2_miflu__L60__seed47__w1` | 571412 | `47da55d1b93f40124d50ad3504d169bed0f3fcddce0959e0818c563549e47225` |
| `primary__gpt2_miflu__L60__seed48__w1` | 571423 | `c69f75aea57e1aaeb4e6a15aea866b86057d84b8118423c4db33b8099030d5b1` |
| `primary__gpt2_miflu__L60__seed49__w1` | 571427 | `b876c3bec286820d2ba692453a59d80bb7819488f674a116582732e5c9692607` |
| `primary__gpt2_miflu__L60__seed50__w1` | 571431 | `ef80c578988d60061a27193f006d6edcf60e1b99ef392a35e1c75c23401852ae` |
| `primary__gpt2_miflu__L60__seed51__w1` | 571441 | `f1a1bb0202dda34b11d992b7043ad8ccdd140a518793c002c0721dc558bfee6d` |

## Provenance gaps (honest, not fabricated)

- `source_full_checkpoint_sha256`: **not recorded** — full checkpoint deleted during v3.15 migration.
- `canonical_tensor_sha256`: **not recorded in v3.15 manifest** — deterministically recomputable from `compact.safetensors`; recomputed at Test time by `test_eval.py`.

## No-change declaration

No model, checkpoint, comparator, prompt, scaler, hyperparameter, endpoint, or rule may change after Test/Holdout access begins. This freeze is append-only and irreversible for the one-time Test phase.
