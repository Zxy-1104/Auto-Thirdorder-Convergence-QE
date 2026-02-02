# 🧪 Test Case: Graphene (Convergence Test)

This folder contains a complete test dataset for **Graphene**. This case is merely a simple run test.

## 📋 Contents

* **Configuration File (`INPUT`)**: Contains 5 convergence test schemes (3x3x1 and 4x4x1 supercells, with different cutoff radii).
* **Pre-calculated Files**: `espresso.ifc2` (2nd-order force constants) and `pseudo/` (pseudopotentials).
* **Structure Files**: Graphene unit cell and supercell templates, and the ShengBTE control file CONTROL.

## 🚀 How to Run the Test

### 1. Preparation
Please ensure that the `templates/` scripts (`sub_calc.sh`, etc.) in the project **root directory** have been configured according to your cluster environment.

> **⚠️ IMPORTANT:**
> Before running the test, you **MUST** open the `INPUT` file in this `TEST/` folder and modify the `THIRDORDER_BIN` variable in the `&cell` section.
> Change it to the **absolute path** of the `thirdorder_espresso.py` script on your system.

### 2. Enter Test Directory
Enter this `TEST` folder in the terminal:

```bash
cd TEST

```

### 3. Run Workflow

You can call the main program from the parent directory or use the absolute path. The program will automatically recognize the `INPUT` file in the current directory and automatically call the `src` library and `templates` scripts from the installation directory.

#### 🔹 Option A: One-Click Automation (Recommended)

```bash
# Call convergence.py from the parent directory
# Run in background: keeps running after logout and saves all output (stdout & stderr) to auto.log
nohup python ../convergence.py auto > auto.log 2>&1 &

# You can also add it to your environment variables

```

#### 🔹 Option B: Step-by-Step (For Debugging)

```bash
python ../convergence.py generate    # Generate files
python ../convergence.py link        # Link files
python ../convergence.py analyze     # Analyze savings
python ../convergence.py submit_dft  # Submit DFT jobs
# ... (Wait for jobs to finish)
python ../convergence.py gen_fc3     # Generate 3rd-order force constants
python ../convergence.py run_bte     # Calculate thermal conductivity
# ... (Wait for jobs to finish)
python ../convergence.py collect     # Collect data
python ../convergence.py plot        # Plotting

```

### 4. Verify Results

After completion, please check if the following content has been generated in the current directory:

* **Folders**: 5 calculation directories (e.g., `thirdorder_331_-2`, etc.).
* **Data**: `kappa_summary.json`.
* **Images**: Convergence curve plots in the `QE_picture/` folder.
