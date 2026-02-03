# Auto-Thirdorder-Convergence-QE

**Automated Workflow for Lattice Thermal Conductivity Convergence (QE & ShengBTE)**

**Auto-Thirdorder-Convergence-QE** is a Python-based automation tool designed to streamline *ab initio* phonon calculations. It specifically targets the tedious process of **convergence testing** for **Supercell Sizes** and **Interaction Cutoffs** in lattice thermal conductivity calculations.

By orchestrating the entire pipeline—from structure generation and DFT submission to 3rd-order force constant extraction and ShengBTE analysis—this tool frees researchers from repetitive manual tasks.

#### 🌟 Key Features

* 🤖 **End-to-End Automation**: One-click `auto` mode handles everything from Phase 1 (Generation) to Phase 5 (Plotting) without manual intervention.
* ⚡ **Smart Deduplication**: Automatically identifies identical atomic structures across different cutoff configurations and uses symlinks to **avoid redundant DFT calculations**, saving 50%+ computational resources.
* 🛡️ **Robust Monitoring**: Uses log-based verification (checks for "Job Done" / "Success") instead of simple queue monitoring, preventing errors caused by filesystem latency.
* 📊 **Auto-Visualization**: Automatically parses output data and generates convergence figures (PRB style) upon completion.
* 🚀 **HPC Friendly**: Native support for the SLURM scheduler, utilizing Job Arrays for efficient massive parallelization.

---

## 📂 Directory Structure

```text
Auto-Thirdorder-Convergence-QE/
├── convergence.py       # Main controller script
├── src/                 # Source code modules
│   ├── generator.py     # Supercell generation
│   ├── deduplicator.py  # Smart linking logic
│   ├── automator.py     # Workflow automation logic
│   └── ...
├── templates/           # Submission script templates (Must Config!)
│   ├── sub_calc.sh      # DFT calculation template
│   ├── sub_gen.sh       # FC3 generation template
│   └── sub_sheng.sh     # ShengBTE template
└── TEST/                # Example test case (Graphene)

```

## 🛠️ Prerequisites

Before using, ensure the following are installed and accessible on your cluster:

1. **Python 3.8+** (with libraries: `numpy`, `matplotlib`)
2. **Quantum Espresso** (v6.x or later, specifically `pw.x`)
3. **ShengBTE** (Executable binary)
4. **Thirdorder** (`thirdorder_espresso.py` script)

---

# 🚀 Usage Guide

## ⚙️ 0. Setup (One-Time Configuration)

To run the workflow conveniently from any directory, setting up an **alias** is recommended.

1. Open your shell configuration file (usually `~/.bashrc`):
```bash
vim ~/.bashrc

```


2. Add the following line (**Use Absolute Path**):
```bash
alias auto-3rd="python /your/absolute/path/to/Auto-Thirdorder-Convergence-QE/convergence.py"

```


3. Apply the changes:
```bash
source ~/.bashrc

```



---

## 📂 1. Preparation

### A. Configure Templates (Crucial!)

Go to the `templates/` directory and edit the `.sh` files to match your cluster environment:

* **Modify `#SBATCH**`: Set correct partition, account, and node constraints.
* **Modify `module load**`: Load your specific Python, MPI, and QE modules.
* **Check Paths**: Ensure `SHENGBTE_EXE` path in `sub_sheng.sh` is correct.
* **⚠️ DO NOT MODIFY `#SBATCH -o**`: Keep `#SBATCH -o reap.out` and `#SBATCH -o shengbte.out` **UNCHANGED**. The automation script relies on these specific log filenames to verify job success.

### B. Prepare Calculation Directory

Ensure your **working directory** contains:

* `INPUT` (Configuration file)
* Structure files: `*_unit.scf.in`, `*_supper.scf.in`
* ShengBTE files: `CONTROL`, `espresso.ifc2`, `pseudo/`

### C. Configure INPUT File

**💡 Tip:** A fully commented template with detailed parameter explanations is available in [`INPUT_example`](./INPUT_example).

**[Important]** Use **Absolute Paths** for scripts in the `INPUT` file to ensure they work from any directory:

```python
&cell
THIRDORDER_BIN = "/path/to/anaconda3/bin/thirdorder_espresso.py"
SUB_GEN_SCRIPT = "/path/to/Auto-Thirdorder-Convergence-QE/templates/sub_gen.sh"

&dft
SUB_SCRIPT = "/path/to/Auto-Thirdorder-Convergence-QE/templates/sub_calc.sh"

&submit
SUB_SCRIPT = "/path/to/Auto-Thirdorder-Convergence-QE/templates/sub_sheng.sh"
...

```

---

## ⚡ 2. Step-by-Step Workflow

If you prefer to run the workflow stage by stage for debugging:

### Phase 1: Pre-processing

```bash
# 1. Generate Supercells
auto-3rd generate

# 2. Structure Deduplication (Create symlinks for equivalent structures)
auto-3rd link

# 3. (Optional) Estimate computational cost savings
auto-3rd analyze

```

### Phase 2: DFT Calculation

```bash
# 4. Submit DFT Jobs
auto-3rd submit_dft

# [WAIT] Use 'squeue' to ensure all 'scf_array' jobs are finished before proceeding.

```

### Phase 3: FC3 & Thermal Conductivity

```bash
# 5. Generate 3rd-Order Force Constants
auto-3rd gen_fc3
# [WAIT] Ensure 'Gen_FC3' jobs are finished.

# 6. Submit ShengBTE Jobs
auto-3rd run_bte
# [WAIT] Ensure 'shengBTE' jobs are finished.

```

### Phase 4: Post-processing

```bash
# 7. Collect Results into JSON
auto-3rd collect

# 8. Plot Convergence Curves
auto-3rd plot

```

---

## 🔥 3. One-Click Automation

The `auto` mode automatically handles submission, monitoring (waiting for queue + I/O sync), and dependency management.

**Recommended Command (Run in background):**

```bash
nohup python /path/to/convergence.py auto > auto.log 2>&1 &

```

*(Note: Using the full path is safer than alias for `nohup`)*

**Monitor Progress:**

```bash
tail -f auto.log

```

### 🛑 How to Stop?

If you need to abort the workflow:

1. **Kill the Controller (Python):**
```bash
ps -ef | grep convergence.py
kill -9 <PID>

```


2. **Cancel Cluster Jobs:**
```bash
squeue -u <your_username>
scancel <JOBID>

```



---

## ❓ Troubleshooting

* **"command not found" in logs**:
* Ensure you loaded necessary modules in the `templates/sub_*.sh` scripts, not just in your current terminal.


* **"Generation failed"**:
* Check if `THIRDORDER_BIN` in `INPUT` is correct.
* Ensure the `thirdorder` python library is installed in the environment loaded by `sub_gen.sh`.


* **"Missing BTE.KappaTensorVsT_CONV"**:
* The ShengBTE job likely crashed. Go to `ShengBTE/task_xxx/` and check `shengbte.out` or `slurm-*.out`. Common causes: missing `CONTROL` file, wrong library paths (`LD_LIBRARY_PATH`), or insufficient memory.


* **"Cost Estimate not found"**:
* Ensure `COST_ESTIMATES` is defined in the `INPUT` file (either under `&analyze` or at the root level).

> **Note:** For more in-depth troubleshooting and workflow logic, please read [`run_guide.txt`](./run_guide.txt).
