#!/bin/bash
#SBATCH -p * # Partition name (Modify according to your cluster)
#SBATCH -N 1
#SBATCH -n 96
#SBATCH --array=1-2    # <--- [KEY] Number of parallel jobs (nodes) for this task
#SBATCH -J scf_array   # <--- [KEY] Job name used by 'automator.py' to monitor status

# ================= User Configuration =================
# [1] Parallel Chunks
NUM_CHUNKS=2    # MUST match the upper limit of '--array' above!

# [2] Computational Resources
MY_NPROC=96     # Total number of cores per node
MY_NPOOL=4      # Quantum Espresso 'npool' parameter

# [3] Environment Setup
source path/to/module.sh
module purge
module load qe/6.7.0-oneAPI.2022.1
# ======================================================

echo "=== Job Array ID: $SLURM_ARRAY_TASK_ID / $NUM_CHUNKS ==="
echo "Work Dir: $(pwd)"

files=($(ls DISP.*.in.* | grep -v ".out" | sort -V))
total_files=${#files[@]}

echo "Total files found: $total_files"

if [ $total_files -eq 0 ]; then
    echo "No files to process. Exiting."
    exit 0
fi

chunk_size=$(( (total_files + NUM_CHUNKS - 1) / NUM_CHUNKS ))
start_idx=$(( (SLURM_ARRAY_TASK_ID - 1) * chunk_size ))
my_batch=("${files[@]:$start_idx:$chunk_size}")

echo "Chunk Size: $chunk_size"
echo "Processing Range: Index $start_idx to $((start_idx + ${#my_batch[@]} - 1))"
echo "Files in this batch: ${#my_batch[@]}"

if [ ${#my_batch[@]} -eq 0 ]; then
    echo "No files assigned to this chunk. Task Done."
    exit 0
fi

for input in "${my_batch[@]}"; do
    output="${input}.out"

    if [ -L "$input" ] || [ -L "$output" ]; then
        echo "Skip Symlink: $input"
        continue
    fi

    if [ -f "$output" ] && grep -q "JOB DONE" "$output"; then
        echo "Skip Completed: $output"
        continue
    fi

    file_num=$(echo "$input" | awk -F'.' '{print $NF}')
    target_outdir="$(pwd)/outdir/job_${file_num}"
    mkdir -p "$target_outdir"

    sed -i -E 's/([0-9])(-[0-9])/\1 \2/g' "$input"
    sed -i "s|outdir.*=.*|outdir = '${target_outdir}'|g" "$input"

    echo ">>> Running: $input"
    mpirun -np $MY_NPROC pw.x -npool $MY_NPOOL -input "$input" > "$output"

    rm -rf "$target_outdir"
done

echo "=== Batch Complete ==="