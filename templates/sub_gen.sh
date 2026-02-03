#!/bin/bash
#SBATCH -p <PARTITION_NAME>    # <--- [USER] Change to your cluster partition
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -J Gen_FC3             # <--- [SYSTEM] DO NOT CHANGE. Used by automator for queue monitoring.
#SBATCH -o reap.out            # <--- [SYSTEM] DO NOT CHANGE. Used by automator to verify 'Success'.

# ================= User Configuration =================
# [1] Environment Setup
# <--- [USER] Load your Python environment below
source /etc/profile.d/modules.sh
module purge
module load python/3.8         # <--- [USER] Ensure this environment has numpy installed

# [2] Note on 'thirdorder_espresso.py'
# The path to the executable is defined in the 'INPUT' file under &cell -> THIRDORDER_BIN.
# You do NOT need to set it here.
# ======================================================
# ... (Rest of the script logic remains unchanged) ...

echo "=== FC3 Generation Job Start ==="
echo "Node: $(hostname)"
echo "Work Dir: $(pwd)"

if [ -z "$THIRDORDER_BIN" ]; then
    echo "Error: THIRDORDER_BIN is missing."
    exit 1
fi

current_folder=$(basename "$(pwd)")
info=${current_folder#thirdorder_}
grid=${info%%_*}
cut=${info##*_}

na=${grid:0:1}
nb=${grid:1:1}
nc=${grid:2:1}

echo "Detected Parameters: na=$na, nb=$nb, nc=$nc, cut=$cut"

if [ -s "FORCE_CONSTANTS_3RD" ]; then
    echo "FORCE_CONSTANTS_3RD already exists. Skipping."
    exit 0
fi

if [ -z "$BASE_INPUT_NAME" ]; then
    BASE_INPUT_NAME=$(ls *.scf.in | grep -v "DISP" | grep -v "suuper" | head -n 1)
fi

echo "Base Input: $BASE_INPUT_NAME"
echo "Binary: $THIRDORDER_BIN"

echo "--- Checking/Linking skipped output files ---"
for f in DISP.*; do
    if [[ "$f" == *".out" ]]; then continue; fi
    
    out_file="${f}.out"
    
    if [ ! -e "$out_file" ]; then
         echo "Warning: Output file $out_file missing!"
    fi
done
echo "--- Check Done ---"

echo "Running reap command..."
ls DISP.*.out | sort -V | "$THIRDORDER_BIN" "$BASE_INPUT_NAME" reap $na $nb $nc $cut

if [ $? -eq 0 ]; then
    echo "Success: FORCE_CONSTANTS_3RD generated."
else
    echo "Error: Generation failed."
    rm -f FORCE_CONSTANTS_3RD 
    exit 1
fi
