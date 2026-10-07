# Environment report (pre-HPC)

## Correction of the earlier “local CPU smoke” description

> **AUDIT NOTE.** The infrastructure/smoke phase was earlier described as a “local CPU smoke”. That was **incorrect**: `torch.cuda.is_available() == True` and every recorded run reports `device: cuda`. The smoke runs actually executed on **cuda:0** (NVIDIA GeForce GTX 1650 with Max-Q Design). The mis-description is corrected here; no result is affected.

## Observed environment

- CUDA available: `True`
- CUDA device count: `1`
- Device name: `NVIDIA GeForce GTX 1650 with Max-Q Design`
- torch: `2.6.0+cu124`

### nvidia-smi

```
Tue Sep 15 05:01:35 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 555.97                 Driver Version: 555.97         CUDA Version: 12.5     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce GTX 1650 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   61C    P8              3W /   35W |       0MiB /   4096MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
                                                                                         
+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI        PID   Type   Process name                              GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
```

## Requested vs actual device per run

| run_id | status | stage | eligible | requested | actual | cuda_avail |
|---|---|---|---|---|---|---|
| `national-ili__dlinear__none__identity__L24__seed42__…` | failed | None | None | None | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | None | None | cuda | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | smoke | False | auto | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | smoke | False | auto | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | smoke | False | auto | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | smoke | False | auto | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | smoke | False | auto | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | smoke | False | auto | cuda | True |
| `national-ili__dlinear__none__identity__L24__seed42__…` | ok | smoke | False | auto | cuda | True |
| `national-ili__fusion-forecaster__gpt2__cross-attenti…` | ok | None | None | cuda | cuda | True |
| `national-ili__fusion-forecaster__gpt2__film-gate__L2…` | ok | None | None | cuda | cuda | True |
| `national-ili__fusion-forecaster__tfidf-svd__concat-p…` | failed | None | None | cuda | cuda | True |
| `national-ili__fusion-forecaster__tfidf-svd__concat-p…` | ok | None | None | cuda | cuda | True |
| `national-ili__gpt2-miflu__gpt2__concat-projection__L…` | ok | None | None | cuda | cuda | True |
| `national-ili__itransformer__none__identity__L24__see…` | failed | None | None | None | cuda | True |
| `national-ili__itransformer__none__identity__L24__see…` | ok | None | None | cuda | cuda | True |
| `national-ili__nlinear__none__identity__L24__seed42__…` | failed | None | None | None | cuda | True |
| `national-ili__nlinear__none__identity__L24__seed42__…` | ok | None | None | cuda | cuda | True |
| `national-ili__patchtst__none__identity__L24__seed42_…` | failed | None | None | None | cuda | True |
| `national-ili__patchtst__none__identity__L24__seed42_…` | ok | None | None | cuda | cuda | True |