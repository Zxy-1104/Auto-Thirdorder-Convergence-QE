import os
import glob
import re
import json
import numpy as np
from collections import defaultdict

def get_kappa_for_temperatures(filepath, target_temps, target_indices):
    if not os.path.exists(filepath):
        return {}
    
    extracted_data = {}
    
    try:
        data = np.loadtxt(filepath)
        if data.ndim == 1:
            data = data.reshape(1, -1)
            
        for row in data:
            current_T = row[0]
            
            for target_T in target_temps:
                if abs(current_T - target_T) < 0.1:
                    values = {}
                    for idx in target_indices:
                        if idx < len(row):
                            values[str(idx)] = float(row[idx])
                    
                    extracted_data[str(target_T)] = values
                    break
                    
    except Exception as e:
        return {}
    
    return extracted_data

def run_collection(config):
    print("--- Starting Results Collection (Multi-Temperature) ---")
    
    temp_cfg = config.get('TEMPERATURE', 300.0)
    target_temps = []
    
    if isinstance(temp_cfg, (int, float)):
        target_temps = [float(temp_cfg)]
    else:
        try:
            target_temps = [float(x.strip()) for x in str(temp_cfg).split(',') if x.strip()]
        except ValueError:
            print(f"Error: Invalid TEMPERATURE format: {temp_cfg}")
            return
            
    target_temps.sort()
    print(f"Target Temperatures (K): {target_temps}")

    target_filename = config.get('TARGET_FILE', 'BTE.KappaTensorVsT_CONV')
    output_json_name = config.get('OUTPUT_JSON', 'kappa_summary.json')
    work_dir = config.get('WORK_DIR', 'ShengBTE')
    root_dir = config.get('ROOT_DIR', '.')
    
    kappa_str = str(config.get('TARGET_KAPPA', '1'))
    try:
        target_indices = [int(x.strip()) for x in kappa_str.split(',') if x.strip()]
    except ValueError:
        print("Error: Invalid format for TARGET_KAPPA.")
        return

    pattern = re.compile(r"task_(\d{3})_(-?\d+)")
    search_path = os.path.join(work_dir, "task_*")
    task_folders = sorted(glob.glob(search_path))
    
    results = defaultdict(dict)
    
    for folder in task_folders:
        folder_name = os.path.basename(folder)
        match = pattern.match(folder_name)
        if not match: continue
        
        sc_raw = match.group(1)
        cutoff = int(match.group(2))
        sc_label = f"{sc_raw[0]}x{sc_raw[1]}x{sc_raw[2]}"
        
        target_file_path = os.path.join(folder, target_filename)
        
        temp_data_map = get_kappa_for_temperatures(target_file_path, target_temps, target_indices)
        
        if temp_data_map:
            results[sc_label][cutoff] = temp_data_map
        else:
            pass 

    headers = ["Cutoff"] + [f"K_{i}" for i in target_indices]
    header_fmt = "{:<10} " + " ".join([f"{{:<12}}" for _ in target_indices])
    
    sorted_sc = sorted(results.keys())
    
    for T in target_temps:
        T_str = str(T)
        print(f"\n{'='*40}")
        print(f" RESULTS FOR T = {T} K")
        print(f"{'='*40}")
        
        for sc in sorted_sc:
            has_data = False
            rows_to_print = []
            
            cutoffs = sorted(results[sc].keys(), key=lambda x: abs(x))
            for cut in cutoffs:
                if T_str in results[sc][cut]:
                    has_data = True
                    vals = results[sc][cut][T_str]
                    cols = [cut] + [f"{vals.get(str(i), 0.0):.4e}" for i in target_indices]
                    rows_to_print.append(cols)
            
            if has_data:
                print(f"\nGrid: {sc}")
                print(header_fmt.format(*headers))
                print("-" * (10 + 13 * len(target_indices)))
                for row in rows_to_print:
                    print(header_fmt.format(*row))

    output_path = os.path.join(root_dir, output_json_name)
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\n[Success] Multi-temp summary saved to: {os.path.abspath(output_path)}")
    except IOError as e:
        print(f"\n[Error] Failed to save JSON: {e}")

if __name__ == "__main__":
    if not os.path.exists("ShengBTE"):
        print("Run via convergence.py")
    else:
        cfg = {
            'TEMPERATURE': "300, 400",
            'TARGET_KAPPA': "1, 5",
            'WORK_DIR': 'ShengBTE', 
            'ROOT_DIR': '.'
        }
        run_collection(cfg)