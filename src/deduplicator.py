import os
import glob
import sys

LOG_FILE = "linking_report.txt"

def parse_structure_fingerprint(filepath):
    nat = 0
    coords = []
    in_positions = False
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith('nat') or 'nat' in line:
                if '=' in line:
                    parts = line.split('=')
                    try:
                        val = parts[1].strip().split(',')[0]
                        nat = int(val)
                    except:
                        pass
                elif line.startswith('nat'):
                     try:
                        parts = line.split()
                        nat = int(parts[1])
                     except:
                        pass

            if 'ATOMIC_POSITIONS' in line:
                in_positions = True
                continue
                
            if in_positions:
                if 'K_POINTS' in line or 'CELL_PARAMETERS' in line:
                    break
                coords.append(line)
        
        if nat == 0 or not coords:
            return None
            
        return (nat, tuple(coords))

    except Exception:
        return None

def create_relative_symlink(src_abs_path, dst_abs_path, log_handle):
    dst_dir = os.path.dirname(dst_abs_path)
    src_rel = os.path.relpath(src_abs_path, dst_dir)
    
    if os.path.islink(dst_abs_path):
        current_target = os.readlink(dst_abs_path)
        if current_target == src_rel:
            return
        os.remove(dst_abs_path)
    elif os.path.exists(dst_abs_path):
        if os.path.getsize(dst_abs_path) > 0:
            return
        os.remove(dst_abs_path)

    os.symlink(src_rel, dst_abs_path)
    
    try:
        root = os.getcwd()
        log_dst = os.path.relpath(dst_abs_path, root)
        log_src = os.path.relpath(src_abs_path, root)
    except:
        log_dst = dst_abs_path
        log_src = src_abs_path
        
    log_handle.write(f"{log_dst} -> {log_src}\n")

def run_linking(configs):
    target_folders = []
    for config in configs:
        na, nb, nc, cut = config
        folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
        target_folders.append(folder_name)

    fingerprint_db = {}
    total_linked = 0
    total_scanned = 0
    
    print("-" * 60)
    print("--- Starting Structure Deduplication (Smart Linking) ---")
    
    with open(LOG_FILE, 'w') as log:
        log.write("=== Thirdorder Duplication Linking Report ===\n")
        
        print("  Phase 1: Indexing existing results...")
        for folder in target_folders:
            if not os.path.exists(folder): continue
            
            inputs = glob.glob(os.path.join(folder, "DISP.*"))
            for infile in inputs:
                if infile.endswith(('.out', '.in', '.save', '.xml', '.run')): continue
                
                outfile = infile + ".out"
                if os.path.exists(outfile) and not os.path.islink(outfile) and os.path.getsize(outfile) > 100:
                    fp = parse_structure_fingerprint(infile)
                    if fp and fp not in fingerprint_db:
                        fingerprint_db[fp] = os.path.abspath(outfile)

        print("  Phase 2: Linking duplicates...")
        for folder in target_folders:
            if not os.path.exists(folder): continue

            input_files = sorted([
                f for f in glob.glob(os.path.join(folder, "DISP.*")) 
                if not f.endswith(('.out', '.in', '.save', '.xml', '.run')) and os.path.isfile(f)
            ])
            
            if not input_files: continue
            
            for infile in input_files:
                fp = parse_structure_fingerprint(infile)
                if fp is None: continue
                
                outfile = infile + ".out"
                abs_outfile = os.path.abspath(outfile)
                
                if fp in fingerprint_db:
                    master_path = fingerprint_db[fp]
                    
                    if master_path == abs_outfile:
                        pass
                    else:
                        create_relative_symlink(master_path, abs_outfile, log)
                        total_linked += 1
                else:
                    fingerprint_db[fp] = abs_outfile
                
                total_scanned += 1

    if total_scanned > 0:
        pct = (total_linked / total_scanned) * 100
    else:
        pct = 0.0

    print("--- Deduplication Complete. ---")
    print(f"    Total Jobs Check: {total_scanned}")
    print(f"    Links Created   : {total_linked} ({pct:.1f}%)")
    print(f"    Details log     : {LOG_FILE}")
    print("-" * 60)