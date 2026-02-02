# Auto-Thirdorder-Convergence-QE
**Automated Workflow for Lattice Thermal Conductivity Convergence (QE & ShengBTE)**

**Auto-Thirdorder-Convergence-QE** is a Python-based automation tool designed to streamline *ab initio* phonon calculations. It specifically targets the tedious process of **convergence testing** for **Supercell Sizes** and **Interaction Cutoffs** in lattice thermal conductivity calculations.

By orchestrating the entire pipeline—from structure generation and DFT submission to 3rd-order force constant extraction and ShengBTE analysis—this tool frees researchers from repetitive manual tasks.

#### 🌟 Key Features
* 🤖 **End-to-End Automation**: One-click `auto` mode handles everything from Phase 1 (Generation) to Phase 5 (Plotting) without manual intervention.
* ⚡ **Smart Deduplication**: Automatically identifies identical atomic structures across different cutoff configurations and uses symlinks to **avoid redundant DFT calculations**, significantly saving computational resources.
* 📊 **Auto-Visualization**: Automatically parses output data and generates figures upon completion.
* 🚀 **HPC Friendly**: Native support for the SLURM scheduler, utilizing Job Arrays for efficient massive parallelization, with support for checkpoint restart and smart path resolution.

# 🚀 Usage Guide

## ⚙️ 0. Setup (One-Time Configuration)

To run the workflow conveniently from any directory, we recommend setting up an **alias**.

1.  Open your shell configuration file (usually `~/.bashrc`):
    ```bash
    vim ~/.bashrc
    ```
2.  Add the following line (replace `/path/to/...` with the actual location where you downloaded this code):
    ```bash
    alias auto-3rd="python /path/to/your/Auto-Thirdorder-Convergence-QE/convergence.py"
    ```
3.  Apply the changes:
    ```bash
    source ~/.bashrc
    ```
    
> **Alternative (If Alias Fails):**
> If you encounter issues setting up the alias or prefer not to use it, you can simply run the script using its absolute path:
> ```bash
> python /path/to/your/Auto-Thirdorder-Convergence-QE/convergence.py [command]
> ```

---

**⚠️ Important Note:** Before running any calculation, you **MUST** go to the **source code installation directory** and configure the submission scripts in `templates/` to match your cluster environment (Partition, Queue, Module load, etc.).

* `templates/sub_calc.sh`
* `templates/sub_gen.sh`
* `templates/sub_sheng.sh`

## 📂 1. Preparation

Ensure your **current working directory** contains:
* `INPUT`, `CONTROL`, `espresso.ifc2`, `pseudo/`, `*_unit.scf.in`, `*_supper.scf.in`.

> **⚠️ IMPORTANT:**
> Before running, you **MUST** open the `INPUT` file and modify the `THIRDORDER_BIN` variable in the `&cell` section.
> Change it to the **absolute path** of the `thirdorder_espresso.py` script on your system (e.g., `/public/home/user/soft/thirdorder/thirdorder_espresso.py`).
> 
## ⚡ 2. Step-by-Step Workflow

If you prefer to run the workflow stage by stage:

### Phase 1: Pre-processing

```bash
# Step 1: Generate Supercells
auto-3rd generate

# Step 2: Structure Deduplication
auto-3rd link

# (Optional) Cost Analysis
auto-3rd analyze

```

### Phase 2: DFT Calculation

```bash
# Step 3: Submit DFT Jobs (Uses templates from install dir)
auto-3rd submit_dft

# ... Wait for DFT jobs to finish ...

# Step 4: Generate 3rd-Order Force Constants
auto-3rd gen_fc3

```

### Phase 3: Thermal Conductivity

```bash
# Step 5: Submit ShengBTE Jobs
auto-3rd run_bte

# ... Wait for ShengBTE jobs to finish ...

```

### Phase 4: Post-processing

```bash
# Step 6: Collect Results
auto-3rd collect

# Step 7: Plot Convergence Curves
auto-3rd plot

```

---

## 🔥 3. One-Click Automation

To execute the entire workflow automatically in the background:

```bash
# Run in background: keeps running after logout and saves all output (stdout & stderr) to auto.log
nohup auto-3rd auto > auto.log 2>&1 &

```

Monitor the progress:

```bash
tail -f auto.log

```

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
