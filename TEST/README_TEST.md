```markdown
# 🧪 Test Case: Graphene (2x2x1)

This folder contains a minimal dataset to verify the workflow functionality. 
It uses a small supercell (2x2x1) and a coarse grid to ensure the test runs quickly (within minutes).

## 📋 Contents
* **Pre-calculated inputs**: `espresso.ifc2` (2nd order force constants) and `pseudo/` (pseudopotentials).
* **Configuration**: A modified `INPUT` file with minimal computational cost settings.
* **Structure files**: Unit cell and Supercell templates for Graphene.

## 🚀 How to Run the Test

1. **Copy Files**:
   Copy all files from this `TEST` directory to the project root directory.
   *(Warning: This will overwrite your existing INPUT file in the root directory)*
   ```bash
   cp -r TEST/* .

```

2. **Check Templates**:
Ensure `templates/*.sh` scripts are configured with your cluster's partition/queue info.
3. **Run Automation**:
Execute the workflow. Since the system is small, you can run it directly (without nohup) to watch the progress.
```bash
python convergence.py auto

```


4. **Verify Output**:
* Check if `thirdorder_221_1/` folder is created.
* Check if `kappa_summary.json` is generated.
* Check if `QE_picture/` contains the convergence plot.



```
