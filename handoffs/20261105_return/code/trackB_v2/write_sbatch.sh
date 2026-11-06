#!/bin/bash
# Generate v2 sbatch wrappers with correct partition / wall / job names.
set -u
R=/gpfs1/scratch/sychan552/trackB_20261104
write_lane () {
  local base="$1" lane="$2" phase="$3" part="$4" wall="$5" gres="$6" nlanes="$7"
  local f="$base/lane${lane}_v2.sbatch"
  local pfx="trackB_v2_${phase}_l${lane}"
  {
    echo '#!/bin/bash'
    echo "#SBATCH --job-name=${pfx}"
    echo "#SBATCH --partition=${part}"
    echo "#SBATCH --gres=${gres}"
    echo '#SBATCH --cpus-per-task=4'
    echo '#SBATCH --mem=48G'
    echo "#SBATCH --time=${wall}"
    echo "#SBATCH --output=${base}/logs/lane${lane}_v2-%j.out"
    echo "#SBATCH --error=${base}/logs/lane${lane}_v2-%j.err"
    echo 'set -u'
    echo "bash ${R}/run_lane_v2.sh ${lane} ${nlanes} ${phase}"
  } > "$f"
}
write_lane "$R/core" 0 core gpu_a100 1-00:00:00 gpu:1 2
write_lane "$R/core" 1 core stingy   1-00:00:00 gpu:a100:1 2
write_lane "$R/all" 0 all gpu_a100 1-00:00:00 gpu:1 3
write_lane "$R/all" 1 all gpu_a100 1-00:00:00 gpu:1 3
# lane2 on stingy: A100 nodes, but QOS partition-stingy caps wall at 06:00:00
# and 1 job/user; the controller resubmits on wall death with validated skips.
write_lane "$R/all" 2 all stingy   06:00:00   gpu:a100:1 3

for phase in core all; do
  base="$R/$phase"
  cat > "$base/controller_v2.sbatch" <<EOF
#!/bin/bash
#SBATCH --job-name=trackB_v2_${phase}_ctl
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=1-00:00:00
#SBATCH --output=${base}/logs/controller_v2-%j.out
#SBATCH --error=${base}/logs/controller_v2-%j.err
set -u
export CONTROLLER_WALL_SECONDS=82800
bash ${R}/controller_v2.sh ${phase}
EOF
done
cat > "$R/all/post_all_v2.sbatch" <<EOF
#!/bin/bash
#SBATCH --job-name=trackB_v2_post_all
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=5-00:00:00
#SBATCH --output=$R/all/logs/post_all_v2-%j.out
#SBATCH --error=$R/all/logs/post_all_v2-%j.err
set -u
bash ${R}/post_all_v2.sh
EOF
echo "GENERATED:"
ls -la "$R"/core/*_v2.sbatch "$R"/all/*_v2.sbatch
