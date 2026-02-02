# 🚀 Usage Guide

## ⚙️ 0. Global Configuration (One-Time Setup)

Before running any calculation, go to the **source code installation directory** and configure the submission scripts in `templates/` to match your cluster environment (Partition, Queue, Module load, etc.).

* `templates/sub_calc.sh`
* `templates/sub_gen.sh`
* `templates/sub_sheng.sh`

## 📂 1. Preparation (Prerequisites)

Ensure your **current working directory** (where you want to run the simulation) contains the following files:

* **`pseudo/`**: Directory containing pseudopotential files (`.UPF`).
* **`CONTROL`**: ShengBTE control file.
* **`espresso.ifc2`**: 2nd-order force constants file.
* **`*_unit.scf.in`**: Unit cell self-consistent field (SCF) input file.
* **`*_supper.scf.in`**: Supercell template file.
* **`INPUT`**: The main configuration file.

## 🛠️ 2. Environment Setup

Ensure you have **Python 3** loaded in your environment.

```bash
# Check available python versions on the cluster
module avail python   

# Load the required python version (replace * with version number, e.g., 3.8)
module load python/* # Verify python version (Ensure it is Python 3.x)
python --version      

```

---

## ⚡ 3. Step-by-Step Workflow

If you prefer to run the workflow stage by stage, follow these commands:

### Phase 1: Pre-processing

```bash
# Step 1: Generate Supercells
# Generates folders and DISP input files for all configurations defined in INPUT.
python convergence.py generate

# Step 2: Structure Deduplication
# Identifies identical atomic structures and creates symlinks to avoid redundant calculations.
python convergence.py link

# (Optional) Cost Analysis
# Analyze how much computational resource is saved by deduplication.
python convergence.py analyze

```

### Phase 2: DFT Calculation (Quantum Espresso)

```bash
# Step 3: Submit DFT Jobs
# Submits Job Arrays. The script automatically uses 'templates/sub_calc.sh' from the install dir.
python convergence.py submit_dft

# ... Wait for all DFT jobs on the cluster to finish ...

# Step 4: Generate 3rd-Order Force Constants
# Automatically checks DFT completeness and calls 'thirdorder_espresso.py reap'.
python convergence.py gen_fc3

```

### Phase 3: Thermal Conductivity (ShengBTE)

```bash
# Step 5: Submit ShengBTE Jobs
# Automatically creates 'ShengBTE/' directory, copies CONTROL/ifc2, and submits jobs.
python convergence.py run_bte

# ... Wait for ShengBTE jobs on the cluster to finish ...

```

### Phase 4: Post-processing

```bash
# Step 6: Collect Results
# Extracts thermal conductivity data from all tasks and generates 'kappa_summary.json'.
python convergence.py collect

# Step 7: Plot Convergence Curves
# Generates PRB-style convergence comparison plots (PNG format) based on collected data.
python convergence.py plot

```

---

## 🔥 4. One-Click Automation (Recommended)

To execute the entire workflow (Phase 1 to 4) automatically in the background:

### Start Automation

Use `nohup` to keep the script running even if your SSH connection drops.

```bash
# You can run this from anywhere using the absolute path or alias
nohup python /path/to/convergence.py auto > auto.log 2>&1 &

```

### Monitor Progress

Check the automation logs in real-time. Press **`Ctrl + C`** to exit the view mode.

```bash
tail -f auto.log

```

### Stop Automation & Cancel Jobs

If you need to stop the workflow halfway:

1. **Kill the Python Script (The Controller):**

```bash
# Find the PID (Process ID)
ps -ef | grep convergence.py

# Kill the process (Replace <PID> with the actual number found above)
kill -9 <PID>

```

2. **Cancel Cluster Jobs (The Calculations):**

```bash
# Check your running jobs
squeue -u <your_username>

# Cancel specific jobs
scancel <JOBID>

# OR Cancel ALL jobs belonging to you (Use with caution!)
scancel -u <your_username>

```

```

```
