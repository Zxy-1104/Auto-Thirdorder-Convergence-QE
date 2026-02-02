```markdown
# 🧪 Test Case: Graphene (Real Convergence Test)

This folder contains a complete dataset for **Graphene** (2D material).

Due to the relatively low computational cost of 2D materials, this dataset acts as a **convergence test**. It simulates the exact procedure used in scientific research to analyze how thermal conductivity converges with supercell size and cutoff radius.

## 📋 Contents

* **Configuration (`INPUT`)**: A realistic configuration file containing 5 specific convergence setups.
* **Pre-calculated Inputs**: `espresso.ifc2` (2nd-order FC) and `pseudo/` (Pseudopotentials).
* **Structure Files**: Unit cell and Supercell templates for Graphene.

## 🚀 How to Run the Test

### 1. Prerequisite
Ensure that the submission scripts in the **project root directory** (`templates/*.sh`) are correctly configured with your cluster's settings.
*(Note: You do NOT need to copy templates here. The software will automatically find them in the installation directory.)*

### 2. Enter Test Directory
Navigate into this `TEST` folder:

```bash
cd TEST

```

### 3. Execute Workflow

Run the main script from the parent directory. The script will use the `INPUT` file in the current directory while loading `src` and `templates` from the installation path.

#### 🔹 Option A: One-Click Automation (Recommended)

```bash
# Run the script located in the parent directory
python ../convergence.py auto

# OR, if you have set up an alias:
# auto-3rd auto

```

#### 🔹 Option B: Step-by-Step (For Debugging)

```bash
python ../convergence.py generate    # Generate files
python ../convergence.py submit_dft  # Submit DFT jobs
# ... (Wait for jobs to finish) ...
python ../convergence.py gen_fc3     # Generate FC3
python ../convergence.py run_bte     # Run ShengBTE
python ../convergence.py collect     # Collect results
python ../convergence.py plot        # Plot convergence

```

### 4. Verify Results

After completion, check the current directory for:

* **Folders**: 5 calculation directories (e.g., `thirdorder_331_-2`).
* **Data**: `kappa_summary.json`.
* **Plots**: Convergence plots in the `QE_picture/` folder.

```
