#!/bin/bash
#SBATCH -p * # Partition name (Modify according to your cluster)
#SBATCH -N 1
#SBATCH -n 96
#SBATCH -J shengBTE    # <--- [KEY] Job name used by 'automator.py' to monitor status

# ================= User Configuration =================
# [1] Computational Resources
MY_NPROC=96  # Number of cores (MUST match #SBATCH -n)

# [2] Software Paths (Please modify to your actual paths)
# Path to Spglib library (ShengBTE dependency)
SPGLIB_LIB_DIR="path/to/your/lib"

# Path to ShengBTE executable
SHENGBTE_EXE="path/to/your/ShengBTE"

# [3] Environment Setup
source /path/to/your/module.sh
module purge
# Load MPI environment (Required by ShengBTE)
module load qe/6.7.0-oneAPI.2022.1 
# ======================================================

echo "=== Job Started at $(date) ==="
echo "Work Dir: $(pwd)"

export LD_LIBRARY_PATH=${SPGLIB_LIB_DIR}:${LD_LIBRARY_PATH}

if [ ! -f "$SHENGBTE_EXE" ]; then
    echo "Error: ShengBTE executable not found at $SHENGBTE_EXE"
    exit 1
fi

REQUIRED_FILES=("CONTROL" "espresso.ifc2" "FORCE_CONSTANTS_3RD")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ] && [ ! -L "$file" ]; then
        echo "Error: Missing input file '$file'"
        exit 1
    fi
done

echo "Starting ShengBTE calculation..."

# 直接运行，输出自动流向 job.out
mpirun -np $MY_NPROC "$SHENGBTE_EXE"

if [ $? -eq 0 ]; then
    echo "Job Done Successfully at $(date)."
else
    echo "Job Failed at $(date)."
    exit 1
fi