import os
import glob
import re
import subprocess
import shutil
import time

def run_reaping(configs, base_input, thirdorder_bin, sub_gen_script):
    print("--- Submitting Force Constants Generation Jobs (Distributed Mode) ---")

    if not os.path.exists(sub_gen_script):
        print(f"Error: Submission script '{sub_gen_script}' not found.")
        print("Please check 'SUB_GEN_SCRIPT' in your INPUT file.")
        return

    script_basename = os.path.basename(sub_gen_script)

    pattern = re.compile(r"thirdorder_(\d+)_(-?\d+)")
    all_folders = sorted(glob.glob("thirdorder_*"))
    
    submit_count = 0
    base_in_name = os.path.basename(base_input)

    for folder in all_folders:
        if not pattern.match(folder): continue
        
        fc3_path = os.path.join(folder, "FORCE_CONSTANTS_3RD")
        if os.path.exists(fc3_path) and os.path.getsize(fc3_path) > 100:
            continue
        
        target_script = os.path.join(folder, script_basename)
        try:
            shutil.copy(sub_gen_script, target_script)
        except IOError as e:
            print(f"  [Error] Failed to copy script to {folder}: {e}")
            continue


        cwd = os.getcwd()
        try:
            os.chdir(folder)

            export_vars = f"ALL,BASE_INPUT_NAME={base_in_name},THIRDORDER_BIN={thirdorder_bin}"
            
            cmd = [
                "sbatch",
                f"--export={export_vars}",
                script_basename
            ]
            
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
            print(f"  [Sub] Submitted job for {folder}")
            submit_count += 1
            
        except subprocess.CalledProcessError as e:
            print(f"  [Error] Failed to submit in {folder}: {e}")
        finally:
            os.chdir(cwd)

    if submit_count == 0:
        print("No new jobs submitted (all folders seem complete).")
    else:
        print(f"--- Successfully submitted {submit_count} jobs. ---")
        print(f"Logs and scripts are located inside each '{pattern.pattern.replace('^', '').replace('$', '')}' folder.")