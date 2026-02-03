# 🧪 Test Case: Graphene (Convergence Test)

This folder contains a complete test dataset for **Graphene**. This case is designed to verify the workflow functionality and test convergence settings.

## 📋 Contents

* **Configuration File (`INPUT`)**: Contains 5 convergence test schemes (3x3x1 and 4x4x1 supercells, with different cutoff radii).
* **Pre-calculated Files**: `espresso.ifc2` (2nd-order force constants) and `pseudo/` (pseudopotentials).
* **Structure Files**: `graphene_unit.scf.in` (Unit cell), `graphene_supper.scf.in` (Supercell template), and `CONTROL` (ShengBTE control file).

## 🛠️ Prerequisites

Before running, ensure the following software is installed and accessible:

1. **Python Environment**: Python 3.8+ with `numpy` and `matplotlib` installed.
2. **Quantum Espresso**: Ensure `pw.x` is available (module loaded in templates).
3. **Thirdorder**: The `thirdorder_espresso.py` script.
4. **ShengBTE**: The `ShengBTE` executable.

## 🚀 How to Run the Test

### 1. Preparation (Crucial!)

1. **Configure Templates**:
* Go to `../templates/` (root directory).
* Edit `sub_calc.sh`, `sub_gen.sh`, and `sub_sheng.sh`.
* **Modify**: Partition (`#SBATCH -p`), Module loading (`module load ...`), and explicitly check `SHENGBTE_EXE` path in `sub_sheng.sh`.


2. **Modify INPUT**:
* Open the `INPUT` file in this directory.
* **[Important]** Change `THIRDORDER_BIN` to the **absolute path** of your `thirdorder_espresso.py`.
* Check `dft` and `submit` sections: Ensure script paths are correct (defaults to `../templates/` using relative paths is fine, but absolute paths are safer).



### 2. Enter Test Directory

```bash
cd TEST

```

### 3. Run Workflow

You can call the main program from the parent directory.

#### 🔹 Option A: One-Click Automation (Recommended)

Since the workflow involves waiting for cluster jobs, use `nohup` to keep it running in the background. **The script will automatically handle job submission, monitoring, and dependency waiting.**

```bash
# Run in background and save logs to 'auto.log'
nohup python ../convergence.py auto > auto.log 2>&1 &

# Monitor progress
tail -f auto.log

```

#### 🔹 Option B: Step-by-Step (For Debugging)

If you want to run step-by-step manually. **Note: For steps involving job submission (`submit_dft`, `gen_fc3`, `run_bte`), you must verify jobs are finished via `squeue` before proceeding to the next step.**

```bash
# 1. Pre-processing
python ../convergence.py generate    # Generate supercell input files
python ../convergence.py link        # Deduplicate structures (Check linking_report.txt)
python ../convergence.py analyze     # Analyze computational savings

# 2. DFT Calculation
python ../convergence.py submit_dft  # Submit QE jobs to cluster
# ... [WAIT] Check 'squeue' until all 'scf_array' jobs are done ...

# 3. Third-order FC Generation
python ../convergence.py gen_fc3     # Submit reap jobs to cluster
# ... [WAIT] Check 'squeue' until 'Gen_FC3' jobs are done ...

# 4. Thermal Conductivity Calculation
python ../convergence.py run_bte     # Submit ShengBTE jobs
# ... [WAIT] Check 'squeue' until 'shengBTE' jobs are done ...

# 5. Post-processing
python ../convergence.py collect     # Collect results to JSON
python ../convergence.py plot        # Plot convergence curves

```

### 4. Verify Results

After completion, please check the following:

* **`linking_report.txt`**: Details of structural deduplication (links created).
* **`kappa_summary.json`**: Collected thermal conductivity data at specified temperatures.
* **`QE_picture/`**: Contains the convergence curve plots.
* **Log Files**: Check `slurm-*.out`, `reap.out`, or `shengbte.out` inside subdirectories if any step fails.

## ❓ Troubleshooting

* **"command not found"**: Check if you have loaded the necessary modules (Python/QE) in your `.bashrc` or the template scripts.
* **"Generation failed" in auto.log**: This often happens if `THIRDORDER_BIN` path is incorrect or the `thirdorder` library is not installed in the current Python environment.
* **"Missing BTE.KappaTensorVsT_CONV"**: ShengBTE job crashed. Go to `ShengBTE/task_xxx/` and check `shengbte.out` or `slurm-*.out` for error messages (e.g., missing library, wrong CONTROL parameters).
