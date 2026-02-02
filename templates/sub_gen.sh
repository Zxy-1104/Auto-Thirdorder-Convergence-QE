#!/bin/bash
#SBATCH -p * # Partition name (Modify according to your cluster)
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -J Gen_FC3     # <--- [KEY] Job name used by 'automator.py' to monitor status

# ================= User Configuration =================
# [1] Environment Setup
source /path/to/your/module.sh
module purge
# Load environment containing 'numpy'
module load python/3.8.6  # <--- Please modify according to your specific environment

# [2] The path to 'thirdorder_espresso.py' is defined in the 'INPUT' file 
#     under the &cell section (THIRDORDER_BIN variable).
# ======================================================

echo "=== FC3 Generation Job Start ==="
echo "Node: $(hostname)"
echo "Work Dir: $(pwd)"

if [ -z "$THIRDORDER_BIN" ]; then
    echo "Error: THIRDORDER_BIN environment variable is not set."
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

echo "--- Linking skipped output files ---"
for f in DISP.*.in.*; do
    if [[ "$f" == *".out" ]]; then continue; fi

    if [ -L "$f" ]; then
        target=$(readlink "$f")
        
        out_link="${f}.out"         
        out_target="${target}.out"    

        if [ -f "$out_target" ] && [ ! -e "$out_link" ]; then
            ln -sf "$out_target" "$out_link"
            # echo "Created ghost link: $out_link -> $out_target"
        fi
    fi
done
echo "--- Linking Done ---"

ls DISP.*.out | sort -V | $THIRDORDER_BIN "$BASE_INPUT_NAME" reap $na $nb $nc $cut

if [ $? -eq 0 ]; then
    echo "Success: FORCE_CONSTANTS_3RD generated."
else
    echo "Error: Generation failed."
    rm -f FORCE_CONSTANTS_3RD 
    exit 1
fi