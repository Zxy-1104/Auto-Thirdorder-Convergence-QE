import os
import glob
import sys

LOG_FILE = "linking_report.txt"

def parse_structure(filepath):
    nat = None
    positions = []
    in_positions = False
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()     
        for line in lines:
            strip_line = line.strip()
            if not strip_line: continue

            if "nat" in line and "=" in line:
                parts = line.split('=')
                try:
                    nat_str = parts[1].split(',')[0].strip()
                    nat = int(nat_str)
                except ValueError: pass
            
            if "ATOMIC_POSITIONS" in line:
                in_positions = True
                continue
            
            if in_positions:
                if "K_POINTS" in line or "CELL_PARAMETERS" in line:
                    break
                
                if nat is not None:
                    positions.append(strip_line)
                    if len(positions) >= nat:
                        break
    except Exception:
        return None, None
    return nat, positions

def create_symlink(src, dst, log_handle):
    abs_src = os.path.abspath(src)
    abs_dst = os.path.abspath(dst)
    if os.path.islink(abs_dst) or os.path.exists(abs_dst):
        os.remove(abs_dst)
    os.symlink(abs_src, abs_dst)
    log_handle.write(f"{dst} -> {src}\n")

def run_linking(configs):
    target_folders = []
    for na, nb, nc, cut in configs:
        target_folders.append(f"thirdorder_{na}{nb}{nc}_{cut}")

    structure_db = {}
    total_linked = 0
    
    print(f"--- Starting Structure Deduplication ---")
    
    with open(LOG_FILE, 'w') as log:
        log.write("=== Thirdorder Duplication Linking Report ===\n")
        log.write("Format: [Target File (Skipped)] -> [Source File (Used)]\n\n")
        
        for folder in target_folders:
            if not os.path.exists(folder):
                continue
                
            print(f"  Processing: {folder} ... ", end='', flush=True)
            
            input_files = sorted([f for f in glob.glob(os.path.join(folder, "DISP.*")) if not f.endswith(".out")])
            folder_link_count = 0
            
            for infile in input_files:
                nat, positions = parse_structure(infile)
                if nat is None or not positions or len(positions) != nat:
                    continue
                
                struct_key = (nat, tuple(positions))
                outfile = infile + ".out"
                
                if struct_key in structure_db:
                    existing_outfile = structure_db[struct_key]
                    create_symlink(existing_outfile, outfile, log)
                    total_linked += 1
                    folder_link_count += 1
                else:
                    structure_db[struct_key] = outfile

            print(f"Done. (Linked: {folder_link_count})")

    print(f"--- Deduplication Complete. Total linked: {total_linked}. See {LOG_FILE}. ---")

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from src.io_utils import ConfigParser
    except ImportError:
        print("Error: Could not import ConfigParser. Please run from project root.")
        sys.exit(1)
        
    config_path = "INPUT"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        
    if not os.path.exists(config_path):
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)
        
    parser = ConfigParser(config_path)
    configs = parser.get('cell', 'configs')
    
    if not configs:
        print("Error: No 'configs' found in INPUT file.")
        sys.exit(1)
        
    run_linking(configs)