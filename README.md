# 🚀 Usage Guide

## ⚙️ 0. Setup (One-Time Configuration)

To run the workflow conveniently from any directory, we recommend setting up an **alias**.

1.  Open your shell configuration file (usually `~/.bashrc`):
    ```bash
    vim ~/.bashrc
    ```
2.  Add the following line (replace `/path/to/...` with the actual location where you downloaded this code):
    ```bash
    alias auto-3rd="python /path/to/your/Auto-Thirdorder-Workflow/convergence.py"
    ```
3.  Apply the changes:
    ```bash
    source ~/.bashrc
    ```
**Note:** Before running any calculation, go to the **source code installation directory** and configure the submission scripts in `templates/` to match your cluster environment (Partition, Queue, Module load, etc.).

* `templates/sub_calc.sh`
* `templates/sub_gen.sh`
* `templates/sub_sheng.sh`

## 📂 1. Preparation

Ensure your **current working directory** contains:
* `INPUT`, `CONTROL`, `espresso.ifc2`, `pseudo/`, `*_unit.scf.in`, `*_supper.scf.in`.

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
nohup auto-3rd auto > auto.log 2>&1 &

```

Monitor the progress:

```bash
tail -f auto.log

```
