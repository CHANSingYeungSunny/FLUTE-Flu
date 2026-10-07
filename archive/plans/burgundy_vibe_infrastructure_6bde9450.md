---
name: burgundy_vibe_infrastructure
overview: Create a suite of scripts (burgundy_smart_launcher.sh for HPC, vibe_gateway.sh for local Windows) that enables automated, self-healing access to CityU's Burgundy HPC cluster as an Ollama-compatible AI API endpoint via SSH tunneling, with intelligent GPU resource selection (A100 priority, A40 fallback) and automatic model downgrading on OOM.
todos:
  - id: create-hpc-launcher
    content: Create burgundy_smart_launcher.sh with cluster auditing, model selection, Ollama execution, and self-healing logic
    status: completed
  - id: create-local-gateway
    content: Create vibe_gateway.sh PowerShell script for job submission, tunnel management, health checking, and global state handling
    status: completed
    dependencies:
      - create-hpc-launcher
  - id: setup-state-directory
    content: Create ~/.burgundy_vibe/ directory structure with config.json, active_node, job_id.txt, blacklist, and logs
    status: completed
    dependencies:
      - create-local-gateway
  - id: verify-integration
    content: "Test end-to-end flow: job submission, tunnel establishment, API health check, and IDE compatibility verification"
    status: completed
    dependencies:
      - create-local-gateway
  - id: document-installation
    content: Create global installation guide with alias setup, directory configuration, and IDE (Cursor/VS Code) integration instructions
    status: completed
    dependencies:
      - verify-integration
---

## Product Overview

A highly robust, global, and fully automated "Vibe Coding" infrastructure that leverages CityU's Burgundy HPC cluster as a free, unlimited AI API endpoint compatible with Cursor, VS Code, Aider, and local CLI tools. The system provides intelligent self-healing capabilities with automatic GPU resource selection (A100 priority, A40 fallback), runtime error recovery, persistent SSH tunneling, and one-click reconnectivity across sessions.

## Core Features

- **Cluster Auditing & Smart Routing**: Before job submission, inspect cluster state via `sinfo`/`squeue` to target idle A100 nodes (Priority 1) or fallback to A40 nodes (Priority 2) across partitions (`gpu_a100`, `stingy`).
- **Dynamic Model Configuration**: 
- A100 path: Attempt `qwen2.5-coder:72b-instruct-q5_K_M` or `deepseek-r1:70b` (~64k+ context)
- A40 fallback: Use `qwen2.5-coder:32b-instruct-q8_0` or `deepseek-coder-v2:16b-lite-instruct-q8_0` for 0-OOM guarantee
- **Runtime Error Analysis & Self-Healing**:
- VRAM OOM: Gracefully terminate crashed instance, step down to lighter model variant, retry on same node
- Node hardware/driver failure: Cancel job, blacklist node, request fresh job on different compute node
- **Automated SSH Keep-Alive Tunneling**: 
- On successful server startup, parse compute node hostname/IP and write to `~/.burgundy_vibe/active_node`
- Local script establishes background SSH tunnel: `-L 11434:compute-node-xx:11434 sychan552@burgundy.hpc.cityu.edu.hk` with keep-alive (`-o ServerAliveInterval=60 -o ServerAliveCountMax=3`)
- **Global Persistence & One-Click Re-connectivity**:
- Unified state directory `~/.burgundy_vibe/` stores job IDs, node info, blacklists, and configuration
- Global command `vibe-on` triggers health check: 
    - If remote job alive: re-establish tunnel to active node
    - If expired/dead: initiate new session from Phase 1
- Local `curl http://localhost:11434` health-loop verifies API readiness for IDE integration

## Tech Stack

- **HPC Cluster Side (Burgundy)**: Bash scripting (Slurm job script)
- **Local Laptop Side (Windows 10/11)**: PowerShell scripting (orchestration engine)
- **AI Inference**: Ollama running inside Singularity container (for cluster security)
- **Communication**: SSH tunneling for local port forwarding
- **State Management**: File-based persistence in `~/.burgundy_vibe/` directory

## Implementation Approach

The solution consists of two coordinated scripts:

1. **burgundy_smart_launcher.sh** (HPC side): Executes within a Slurm job on allocated compute node. Performs real-time cluster auditing to determine optimal GPU type (A100/A40), dynamically selects model size, launches Ollama in Singularity, monitors stderr/stdout for errors, and implements self-healing logic (model downgrade on OOM, job cancellation/resubmission on node failure).
2. **vibe_gateway.sh** (Local side): PowerShell script that manages the end-to-end lifecycle. Checks for existing active jobs/tunnels, submits new Slurm jobs with optimized parameters when needed, establishes/maintains SSH tunnels with keep-alive, and provides health verification. Uses `~/.burgundy_vibe/` for global state persistence across sessions.

Key technical decisions:

- **Resource Selection Logic**: Uses `sinfo -o "%P %D %C %t %G"` to parse partition, node count, core count, state, and GPU features. Targets partitions `gpu_a100` (A100-40G) and `stingy` (mixed including A100/A40) based on HPC_GUIDE.md specifications.
- **Self-Healing Granularity**: Model downgrade follows predefined tiers (72B→32B→16B) to minimize restart latency while maintaining usability. Node blacklisting is session-only to avoid permanent exclusion.
- **Tunnel Reliability**: SSH keep-alive parameters prevent connection drops during idle periods. Tunnel establishment waits for node IP availability from job startup logs.
- **Windows Compatibility**: Local script uses PowerShell-native SSH client (available in Windows 10/1809+) and stores state in `%USERPROFILE%\.burgundy_vibe\` for global accessibility.

## Architecture Design

### System Architecture

- **Layered Design**: 
- Presentation Layer: Local IDE/CLI tools accessing `http://localhost:11434`
- Tunnel Layer: SSH local port forwarding (`localhost:11434` → `compute-node:11434`)
- Service Layer: Ollama API server running in Singularity container on HPC compute node
- Orchestration Layer: `vibe_gateway.sh` (local) and `burgundy_smart_launcher.sh` (HPC)
- Resource Layer: Burgundy HPC cluster Slurm scheduler and compute nodes
- **Data Flow**: 
Local health check → Job submission (if needed) → Slurm allocation → Node boot → Environment setup → Ollama startup → Health verification → Tunnel activation → IDE communication
- **Failure Handling**: 
OOM detected → Model downgrade → Same-node restart → Hardware error → Job cancel → Blacklist → New job submission

### Directory Structure

```
c:/Users/Asus/Desktop/FYP code/MLFlu/
├── scripts/
│   ├── burgundy_smart_launcher.sh   # [NEW] HPC-side launcher (self-healing Ollama runner)
│   └── vibe_gateway.sh              # [NEW] Local-side PowerShell orchestrator
└── ~/.burgundy_vibe/                # [NEW] Global state directory (Windows: %USERPROFILE%\.burgundy_vibe\)
    ├── config.json                  # Default model tiers, timeouts, partitions
    ├── active_node                  # Current compute node hostname/IP
    ├── job_id.txt                   # Active Slurm job ID
    ├── node_blacklist.txt           # Session-only failed node IDs
    └── logs/                        # Execution logs for debugging
```

## Implementation Details

### Environment Setup (HPC Side)

- Module purge/load: `module unload default && module load old_modules`
- Conda activation via PATH: `export PATH="/home/sychan552/.conda/envs/mlflu_hpc:$PATH"`
- HF cache: `export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache`
- Singularity container execution: `singularity exec --nv /path/to/ollama.sif ollama serve`

### Error Detection Patterns

- OOM: Match `(?i)out of memory|cuda_error_out_of_memory|allocation failed`
- Node failure: Match `(?i)cuda-capable device busy|ecc error|driver version mismatch|illegal memory access`

### Model Management

- Models cached in Singularity container or pulled via `ollama pull` at startup
- Fallback chain: 72B/70B → 32B/16B → (optional) 7B if all fail
- Context window preserved where possible during downgrades