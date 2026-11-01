#!/bin/bash
# Locate conda on the CityU login node (it is a module here, but the module may
# not be loadable - find the real binary that created mlflu_hpc).
echo '--- module avail (conda) ---'
module avail 2>&1 | grep -i conda | head -20
echo '--- module spider conda ---'
module spider Conda 2>&1 | head -20
echo '--- candidate conda binaries ---'
for p in /home/sychan552/miniconda3/bin/conda \
         /home/sychan552/anaconda3/bin/conda \
         /home/sychan552/.conda/bin/conda \
         /home/sychan552/scratch/miniconda3/bin/conda \
         /home/sychan552/scratch/anaconda3/bin/conda \
         /opt/conda/bin/conda ; do
    if [ -x "$p" ]; then echo "FOUND $p"; fi
done
echo '--- top-level home dirs matching conda ---'
ls -d /home/sychan552/*conda* 2>/dev/null
echo '--- .conda ---'
ls -l /home/sychan552/.conda/ 2>&1 | head -20
echo '--- mlflu_hpc python real path ---'
readlink -f /home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo '--- conda-meta presence ---'
ls /home/sychan552/.conda/envs/mlflu_hpc/conda-meta/*.json 2>/dev/null | wc -l
echo END
