import os
import glob
import re
import shutil
import subprocess
import sys

def submit_jobs(config):
    root_dir = config.get('ROOT_DIR', '.')
    work_dir = config.get('WORK_DIR', 'ShengBTE')
    control_file = config.get('CONTROL_FILE', 'CONTROL')
    ifc2_file = config.get('IFC2_FILE', 'espresso.ifc2')
    sub_script_tpl = config.get('SUB_SCRIPT', 'templates/sub_sheng.sh')
    target_result = config.get('TARGET_RESULT', 'BTE.KappaTensorVsT_CONV')

    required_files = [control_file, ifc2_file, sub_script_tpl]
    for f in required_files:
        if not os.path.exists(f):
            print(f"Error: Required file '{f}' not found in root directory.")
            return

    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
        print(f"Created working directory: {work_dir}")

    pattern = re.compile(r"thirdorder_(\d+)_(-?\d+)")
    source_folders = sorted(glob.glob(os.path.join(root_dir, "thirdorder_*")))
    
    print(f"--- Starting ShengBTE Submission ---")
    print(f"Found {len(source_folders)} candidate folders.")

    skipped_count = 0
    submitted_count = 0

    for src_folder in source_folders:
        folder_name = os.path.basename(src_folder)
        match = pattern.match(folder_name)
        if not match: continue

        sc_size = match.group(1)
        cutoff = match.group(2)
        
        fc3_path = os.path.join(src_folder, "FORCE_CONSTANTS_3RD")
        if not os.path.exists(fc3_path):
            continue

        task_folder_name = f"task_{sc_size}_{cutoff}"
        task_dir = os.path.join(work_dir, task_folder_name)

        result_path = os.path.join(task_dir, target_result)
        if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
            print(f"  [Skip] {task_folder_name}: Result exists.")
            skipped_count += 1
            continue

        if not os.path.exists(task_dir):
            os.makedirs(task_dir)

        abs_control = os.path.abspath(control_file)
        abs_ifc2 = os.path.abspath(ifc2_file)
        abs_fc3 = os.path.abspath(fc3_path)
        abs_sub_script = os.path.abspath(sub_script_tpl)

        shutil.copy(abs_control, os.path.join(task_dir, "CONTROL"))

        dest_ifc2 = os.path.join(task_dir, "espresso.ifc2")
        if not os.path.exists(dest_ifc2):
            os.symlink(abs_ifc2, dest_ifc2)

        dest_fc3 = os.path.join(task_dir, "FORCE_CONSTANTS_3RD")
        if os.path.exists(dest_fc3) or os.path.islink(dest_fc3):
            os.remove(dest_fc3)
        os.symlink(abs_fc3, dest_fc3)

        dest_script_name = os.path.basename(sub_script_tpl)
        shutil.copy(abs_sub_script, os.path.join(task_dir, dest_script_name))

        original_cwd = os.getcwd()
        try:
            os.chdir(task_dir)
            
            job_name = f"K_{sc_size}_{cutoff}"
            print(f"  [Sub] Submitting {task_folder_name} ...")
            
            cmd = f"sbatch -J {job_name} {dest_script_name}"
            
            ret = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)
            if ret == 0:
                submitted_count += 1
            else:
                print(f"    Error: Submission failed for {task_folder_name}")
                
        except Exception as e:
            print(f"    Error in {task_folder_name}: {e}")
        finally:
            os.chdir(original_cwd)

    print(f"\n--- Submission Summary ---")
    print(f"  Skipped (Done) : {skipped_count}")
    print(f"  Submitted      : {submitted_count}")