import os
import shutil
import subprocess
import sys

def run_command(cmd, work_dir):
    try:
        script_path = cmd.split()[0]
        if os.path.exists(script_path) and not os.access(script_path, os.X_OK):
            os.chmod(script_path, 0o755)
        subprocess.run(cmd, shell=True, cwd=work_dir, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[Error] Command failed in {work_dir}: {cmd}")
        print(f"Error Message: {e.stderr.decode().strip()}")
        return False
    return True

def run_generation(configs, base_input, tpl_name, thirdorder_bin):
    print("-" * 60)
    print("--- Starting Supercell Generation (Phase 1) ---")
    
    if not configs: return []
    if not os.path.exists(base_input):
        print(f"Error: Base input '{base_input}' not found.")
        return []

    has_template = False
    if tpl_name and os.path.exists(tpl_name):
        has_template = True
    elif tpl_name:
        print(f"Error: Template '{tpl_name}' defined in INPUT but not found.")
        return []

    generated_folders = []

    for config in configs:
        na, nb, nc, cut = config
        folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
        generated_folders.append(folder_name)
        
        if os.path.exists(os.path.join(folder_name, "FORCE_CONSTANTS_3RD")):
            print(f"  [Skip] {folder_name} (Completed)")
            continue
        
        has_disp = False
        if os.path.exists(folder_name):
             files = os.listdir(folder_name)
             if any(f.startswith("DISP.") and not f.endswith(".in") for f in files):
                 has_disp = True
        
        if has_disp:
             print(f"  [Skip] {folder_name} (Generated)")
             continue

        print(f"  [Gen] Generating {folder_name} ...")
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        shutil.copy(base_input, os.path.join(folder_name, base_input))
        
        if has_template:
            shutil.copy(tpl_name, os.path.join(folder_name, tpl_name))
            cmd = f"{thirdorder_bin} {base_input} sow {na} {nb} {nc} {cut} {tpl_name}"
        else:
            cmd = f"{thirdorder_bin} {base_input} sow {na} {nb} {nc} {cut}"
        
        success = run_command(cmd, work_dir=folder_name)
        if not success:
            print(f"    [Failed] Generation failed for {folder_name}")
        
    print(f"--- Generation Complete. ---")
    print("-" * 60)
    return generated_folders