import os
import glob
import re
import subprocess
import shutil

def submit_dft_jobs(config):
    print("--- Starting DFT Submission (Shell-Controlled) ---")

    template_script = config.get('SUB_SCRIPT', 'templates/sub_calc.sh')
    
    if not os.path.exists(template_script):
        print(f"Error: Template script '{template_script}' not found.")
        return

    pattern = re.compile(r"thirdorder_(\d{3})_(-?\d+)")
    folders = sorted(glob.glob("thirdorder_*"))
    
    submit_count = 0
    
    for folder in folders:
        if not pattern.match(folder): continue
        
        input_files = glob.glob(os.path.join(folder, "DISP.*.in.*"))
        input_files = [f for f in input_files if not f.endswith(".out")]

        if not input_files:
            print(f"  [Skip] {folder}: No DISP files found.")
            continue
            
        print(f"  [Sub] Submitting folder: {folder}")
        
        local_script_name = "run_dft.sh"
        local_script_path = os.path.join(folder, local_script_name)
        shutil.copy(template_script, local_script_path)
        
        job_name = f"DFT_{folder.replace('thirdorder_', '')}"
        
        cmd = [
            "sbatch",
            f"--job-name={job_name}",
            local_script_name
        ]
        
        full_cmd = " ".join(cmd)
        
        cwd = os.getcwd()
        try:
            os.chdir(folder)
            subprocess.call(full_cmd, shell=True)
            submit_count += 1
        except Exception as e:
            print(f"Error submitting in {folder}: {e}")
        finally:
            os.chdir(cwd)
            
    print(f"--- DFT Submission Complete. {submit_count} folders processed. ---")