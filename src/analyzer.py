import os
import glob
import re
import sys
from collections import defaultdict

LOG_FILE = "linking_report.txt"

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

def run_analysis(cost_estimates):
    pattern = re.compile(r"thirdorder_(\d+)_(-?\d+)")
    folders = sorted(glob.glob("thirdorder_*"))
    
    data = defaultdict(list)
    
    for folder in folders:
        match = pattern.match(folder)
        if not match: continue
        
        sc_str = match.group(1)
        cut_str = match.group(2)
        
        total, saved = get_folder_stats(folder)
        
        if total == 0:
            continue

        data[sc_str].append({
            'cut': cut_str,
            'total': total,
            'saved': saved
        })

    with open(LOG_FILE, 'a') as f:
        f.write("\n" + "="*85 + "\n")
        f.write("COMPUTATIONAL COST SAVINGS ANALYSIS (Weighted by Core-Hours)\n")
        f.write("="*85 + "\n")
        
        grand_total_saved_hours = 0.0
        grand_total_potential_hours = 0.0 

        for sc in sorted(data.keys()):
            if sc not in cost_estimates:
                f.write(f"\n[WARNING] No cost estimate found for Supercell {sc}. Assuming 0.\n")
                unit_cost = 0
            else:
                unit_cost = cost_estimates[sc]

            f.write(f"\nSupercell {sc} (Est. Cost: {unit_cost} Core-Hours/Job)\n")
            f.write(f"{'-'*85}\n")
            f.write(f"{'Cutoff':<10} | {'Total Jobs':<12} | {'Linked(Saved)':<15} | {'Actual Run':<12} | {'Savings %':<10}\n")
            f.write(f"{'-'*85}\n")

            sc_total_jobs = 0
            sc_total_saved = 0
            
            entries = sorted(data[sc], key=lambda x: abs(int(x['cut'])))

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
            f.write(f"SUBTOTAL {sc}:\n")
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
    print(f"--- Analysis Complete. Results appended to {LOG_FILE}. ---")


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from src.io_utils import ConfigParser
    except ImportError:
        sys.exit(1)
        
    config_path = "INPUT"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        
    if not os.path.exists(config_path):
        sys.exit(1)
        
    parser = ConfigParser(config_path)
    costs = parser.get('analyze', 'COST_ESTIMATES')
    
    if not costs:
        sys.exit(1)
        
    run_analysis(costs)