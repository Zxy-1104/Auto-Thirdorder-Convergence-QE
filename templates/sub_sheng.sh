#!/bin/bash
#SBATCH -p <PARTITION_NAME>    # <--- [USER] Change to your cluster partition
#SBATCH -N 1
#SBATCH -n 96                  # <--- [USER] Change to cores per node
#SBATCH -J shengBTE            # <--- [SYSTEM] DO NOT CHANGE. Used by automator for queue monitoring.
#SBATCH -o shengbte.out        # <--- [SYSTEM] DO NOT CHANGE. Used by automator to verify 'Job Done'.

# ================= User Configuration =================
# [1] Computational Resources
MY_NPROC=96  # <--- [USER] MUST match #SBATCH -n above

# [2] Software Paths
# <--- [USER] Set the absolute path to your Spglib library (ShengBTE dependency)
SPGLIB_LIB_DIR="/path/to/your/spglib/lib"

# <--- [USER] Set the absolute path to your ShengBTE executable
SHENGBTE_EXE="/path/to/your/ShengBTE"

# [3] Environment Setup
# <--- [USER] Load your MPI/Compiler environment below
source /etc/profile.d/modules.sh
module purge
module load qe/6.7.0           # <--- [USER] Load MPI environment required by ShengBTE
# ======================================================
# ... (Rest of the script logic remains unchanged) ...

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

mpirun -np $MY_NPROC "$SHENGBTE_EXE"

if [ $? -eq 0 ]; then
    echo "Job Done Successfully at $(date)."
else
    echo "Job Failed at $(date)."
    exit 1
fi
