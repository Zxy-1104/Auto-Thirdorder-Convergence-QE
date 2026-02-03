import os
import glob
import re
from collections import defaultdict

def get_folder_stats(folder_path):
    try:
        all_files = os.listdir(folder_path)
    except FileNotFoundError:
        return 0, 0

    jobs_status = {}

    for f in all_files:
        if not f.startswith("DISP."):
            continue

        parts = f.split('.')
        job_id = None

        if parts[-1].isdigit():
            job_id = parts[-1]
        elif parts[-1] == 'out' and len(parts) >= 2 and parts[-2].isdigit():
            job_id = parts[-2]
        
        if job_id:
            if job_id not in jobs_status:
                jobs_status[job_id] = False
            
            full_path = os.path.join(folder_path, f)
            if os.path.islink(full_path):
                jobs_status[job_id] = True

    total = len(jobs_status)
    linked = sum(jobs_status.values())
    return total, linked

def run_analysis(analyze_cfg):
    LOG_FILE = "linking_report.txt"
    cost_map = analyze_cfg.get('COST_ESTIMATES', {})

    pattern = re.compile(r"thirdorder_(\d+)_(-?\d+)")
    folders = sorted(glob.glob("thirdorder_*"))
    
    data = defaultdict(list)
    found_sc_keys = set()

    print(f"--- Analyzing Computational Savings ---")

    for folder in folders:
        match = pattern.match(folder)
        if not match: continue
        
        sc_str = match.group(1)
        cut_str = match.group(2)
        
        total, saved = get_folder_stats(folder)

        data[sc_str].append({
            'cut': cut_str,
            'total': total,
            'saved': saved
        })
        found_sc_keys.add(sc_str)

    print(f"Generating analysis report to {LOG_FILE}...")
    
    with open(LOG_FILE, 'a') as f:
        f.write("\n\n")
        f.write("="*85 + "\n")
        f.write("COMPUTATIONAL COST SAVINGS ANALYSIS (Weighted by Core-Hours)\n")
        f.write("="*85 + "\n")
        
        grand_total_saved_hours = 0.0
        grand_total_potential_hours = 0.0 

        all_sc_keys = found_sc_keys.union(set(cost_map.keys()))

        for sc in sorted(list(all_sc_keys)):
            sc_key = str(sc) 
            
            if sc_key not in cost_map:
                f.write(f"\n[WARNING] No cost estimate found for Supercell {sc_key}. Assuming 0.\n")
                unit_cost = 0.0
            else:
                unit_cost = float(cost_map[sc_key])
            
            if sc_key not in data:
                continue

            f.write(f"\nSupercell {sc_key} (Est. Cost: {unit_cost} Core-Hours/Job)\n")
            f.write(f"{'-'*85}\n")
            f.write(f"{'Cutoff':<10} | {'Total Jobs':<12} | {'Linked(Saved)':<15} | {'Actual Run':<12} | {'Savings %':<10}\n")
            f.write(f"{'-'*85}\n")

            sc_total_jobs = 0
            sc_total_saved = 0
            
            entries = sorted(data[sc_key], key=lambda x: abs(int(x['cut'])))

            if not entries:
                f.write(f"  (No folders found yet for Supercell {sc_key})\n")

            for entry in entries:
                cut = entry['cut']
                t = entry['total']
                s = entry['saved']
                a = t - s
                
                pct = (s / t * 100) if t > 0 else 0.0
                
                f.write(f"{cut:<10} | {t:<12} | {s:<15} | {a:<12} | {pct:8.1f}%\n")
                
                sc_total_jobs += t
                sc_total_saved += s
            
            sc_pct = (sc_total_saved / sc_total_jobs * 100) if sc_total_jobs > 0 else 0.0
            
            saved_hours = sc_total_saved * unit_cost
            potential_hours = sc_total_jobs * unit_cost
            
            grand_total_saved_hours += saved_hours
            grand_total_potential_hours += potential_hours
            
            f.write(f"{'-'*85}\n")
            f.write(f"SUBTOTAL {sc_key}:\n")
            f.write(f"  - Jobs Saved: {sc_total_saved}/{sc_total_jobs} ({sc_pct:.1f}%)\n")
            f.write(f"  - Hours Saved: {saved_hours:,.1f} Core-Hours\n")
            f.write(f"{'='*85}\n")

        if grand_total_potential_hours > 0:
            weighted_pct = (grand_total_saved_hours / grand_total_potential_hours) * 100
        else:
            weighted_pct = 0.0

        f.write(f"\nFINAL REPORT:\n")
        f.write(f"  Overall Savings (%)   : {weighted_pct:.1f}%\n")
        f.write(f"  TOTAL COMPUTING SAVED : {grand_total_saved_hours:,.1f} Core-Hours\n")
        f.write(f"{'='*85}\n")
        
    print(f"--- Analysis Complete. Results saved to {LOG_FILE}. ---")