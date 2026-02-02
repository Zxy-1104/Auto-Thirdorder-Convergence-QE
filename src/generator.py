import os
import shutil
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

def run_command(cmd, work_dir):
    try:
        subprocess.check_call(cmd, shell=True, cwd=work_dir, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        sys.stderr.write(f"Error running command in {work_dir}: {cmd}\n")
        sys.exit(1)

def run_generation(configs, base_input, tpl_name, thirdorder_bin="thirdorder_espresso.py"):
    print("--- Starting Supercell Generation (In-place Mode) ---")
    
    if not os.path.exists(base_input):
        print(f"Error: Base input file '{base_input}' not found.")
        return []

    if tpl_name and not os.path.exists(tpl_name):
        print(f"Error: Template file '{tpl_name}' not found.")
        return []

    generated_folders = []

    for config in configs:
        na, nb, nc, cut = config
        folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
        generated_folders.append(folder_name)
        
        if os.path.exists(folder_name):
             print(f"  [Skip] Folder '{folder_name}' already exists.")
             continue

        print(f"  [Gen] Generating {folder_name} (Grid: {na}x{nb}x{nc}, Cut: {cut})...")
        
        os.makedirs(folder_name)

        shutil.copy(base_input, os.path.join(folder_name, base_input))
        
        if tpl_name:
            shutil.copy(tpl_name, os.path.join(folder_name, tpl_name))
        
        cmd = f"{thirdorder_bin} {base_input} sow {na} {nb} {nc} {cut} {tpl_name}"
        
        run_command(cmd, work_dir=folder_name)
        
    print(f"--- Generation Complete. {len(generated_folders)} folders processed. ---")
    return generated_folders