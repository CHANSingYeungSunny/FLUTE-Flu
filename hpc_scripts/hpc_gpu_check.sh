#!/bin/bash
echo "=== sinfo summary ==="
sinfo -s
echo
echo "=== all nodes: partition | node | state | gres (A100/A40 highlighted) ==="
sinfo -o "%P|%N|%t|%G" | sort
echo
echo "=== IDLE A100 nodes (any partition) ==="
sinfo -t idle -h -o "%P %N %t %G" | grep -i a100 || echo "  (none idle)"
echo
echo "=== IDLE A40 nodes (any partition) ==="
sinfo -t idle -h -o "%P %N %t %G" | grep -i a40 || echo "  (none idle)"
echo
echo "=== MIXED/idle nodes that could yield a GPU soon ==="
sinfo -t idle,mixed -h -o "%P %N %t %G"
echo
echo "=== my queue ==="
squeue -u sychan552
