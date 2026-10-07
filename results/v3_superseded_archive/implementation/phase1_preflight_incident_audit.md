# Phase 1 preflight incident audit

Classification: **BEHAVIOR_NEUTRAL_PRE_PILOT_PROCESS_VIOLATION**.

The initial static Pilot metadata generation called `make_backbone()` from `hpc_specs._arch_report`. For `gpt2_miflu`, that imported and constructed the existing MIFlu/GPT-2 adapter. This was a process violation because model construction occurred locally rather than in a Slurm compute-node job.

The audit found zero forward/backward passes, training, inference, evaluation, predictions, metrics, checkpoints, result figures, Test/holdout reads, Slurm submissions, Qwen downloads, or Pilot jobs attributable to this incident. Remote lightweight evidence showed an empty current queue, no remote v3 deployment root, no remote v3 script root, and no Qwen cache. Two historical completed jobs (`560659`, `560692`) were not Phase 1 jobs and had no v3/Pilot artifact linkage.

The defect is repaired: metadata generation now uses static declarations only, and the architecture/Pilot tests avoid constructing real model objects. This audit and the original incident record are preserved; no result is ranked or used for v3 design.
