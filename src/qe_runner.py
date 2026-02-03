import os
import glob
import re
import subprocess
import shutil

def submit_dft_jobs(config):
    print("-" * 60)
    print("--- Starting DFT Submission (Phase 2) ---")

    raw_script = config.get('SUB_SCRIPT', 'templates/sub_calc.sh')
    template_script = os.path.abspath(raw_script)
    
    if not os.path.exists(template_script):
        print(f"Error: Template script '{template_script}' not found.")
        return

    pattern = re.compile(r"thirdorder_(\d+)_(-?\d+)")
    folders = sorted(glob.glob("thirdorder_*"))
    
    submit_count = 0
    
    for folder in folders:
        if not pattern.match(folder): continue
        
        all_files = glob.glob(os.path.join(folder, "DISP.*"))
        input_files = [
            f for f in all_files 
            if not f.endswith(".out") 
            and not f.endswith(".run") 
            and not f.endswith(".save") 
            and not f.endswith(".xml")
        ]

        if not input_files:
            print(f"  [Skip] {folder}: No DISP input files found.")
            continue
            
        print(f"  [Sub] Submitting folder: {folder} ({len(input_files)} jobs)")
        
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
    print("-" * 60)