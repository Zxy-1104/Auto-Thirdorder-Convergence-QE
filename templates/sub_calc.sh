#!/bin/bash
#SBATCH -p <PARTITION_NAME>    # <--- [USER] Change to your cluster partition (e.g., v6_384)
#SBATCH -N 1
#SBATCH -n 96                  # <--- [USER] Change to cores per node
#SBATCH --array=1-2            # <--- [USER] Adjust job array size based on your resource limit
#SBATCH -J scf_array           # <--- [SYSTEM] DO NOT CHANGE. Used by automator for queue monitoring.

# ================= User Configuration =================
# [1] Parallel Chunks
# NOTE: This number MUST match the upper limit of '--array' above!
NUM_CHUNKS=2

# [2] Computational Resources
MY_NPROC=96      # <--- [USER] Total number of cores per node
MY_NPOOL=4       # <--- [USER] Quantum Espresso 'npool' parameter

# [3] Environment Setup
# <--- [USER] Load your specific modules below
source /etc/profile.d/modules.sh
module purge
module load qe/6.7.0             # <--- [USER] Modify to your QE module
# ======================================================
# ... (Rest of the script logic remains unchanged) ...
# (Only the header needs to be exposed for configuration)

echo "=== Job Array ID: $SLURM_ARRAY_TASK_ID / $NUM_CHUNKS ==="
echo "Work Dir: $(pwd)"

files=($(ls DISP.* | grep -v "\.out$" | grep -v "\.save$" | grep -v "\.xml$" | grep -v "\.run$" | sort -V))
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
        echo "Skip Symlink (Deduplicated): $input"
        continue
    fi

    if [ -f "$output" ] && grep -q "JOB DONE" "$output"; then
        echo "Skip Completed: $output"
        continue
    fi

    file_num=$(echo "$input" | awk -F'.' '{print $NF}')
    target_outdir="$(pwd)/outdir/job_${file_num}"
    
    run_input="${input}.run"
    cp "$input" "$run_input"

    mkdir -p "$target_outdir"

    sed -i "/outdir/d" "$run_input" 
    sed -i "/&CONTROL/a \ \ outdir = '${target_outdir}'" "$run_input"

    echo ">>> Running: $input (ID: $file_num)"

    mpirun -np $MY_NPROC pw.x -npool $MY_NPOOL -input "$run_input" > "$output"

    rm -rf "$target_outdir"
    rm -f "$run_input"
done

echo "=== Batch Complete ==="
