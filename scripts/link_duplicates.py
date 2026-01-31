#!/usr/bin/env python3
import os
import glob
import sys

# 导入配置
try:
    from generate_cells import configs
except ImportError:
    print("Error: Could not import 'configs' from 'generate_cells.py'.")
    sys.exit(1)

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
            if not strip_line: continue # 跳过空行

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
                # [优化] 如果读到了下一个板块（比如 K_POINTS），停止读取坐标
                if "K_POINTS" in line or "CELL_PARAMETERS" in line:
                    break
                
                if nat is not None:
                    # 我们不需要在这里修复格式，只要把这一行的字符串存下来
                    # 即使它是粘连的，相同结构的粘连方式也一样，所以可以查重
                    positions.append(strip_line)
                    if len(positions) >= nat:
                        break
    except Exception as e:
        return None, None
    return nat, positions

def create_symlink(src, dst, log_handle):
    abs_src = os.path.abspath(src)
    abs_dst = os.path.abspath(dst)
    # 如果目标已经是链接或文件，先删除
    if os.path.islink(abs_dst) or os.path.exists(abs_dst):
        os.remove(abs_dst)
    os.symlink(abs_src, abs_dst)
    log_handle.write(f"{os.path.basename(dst)} -> {src}\n")

def main():
    target_folders = []
    for na, nb, nc, cut in configs:
        target_folders.append(f"thirdorder_{na}{nb}{nc}_{cut}")

    structure_db = {}
    total_linked = 0
    
    with open(LOG_FILE, 'w') as log:
        log.write("=== Thirdorder Duplication Linking Report ===\n")
        
        for folder in target_folders:
            if not os.path.exists(folder): continue
                
            print(f"Processing folder: {folder} ... ", end='', flush=True)
            
            # 这里的排序保证先处理编号小的文件（作为源文件）
            input_files = sorted([f for f in glob.glob(os.path.join(folder, "DISP.*")) if not f.endswith(".out")])
            folder_link_count = 0
            
            for infile in input_files:
                nat, positions = parse_structure(infile)
                # 只有当解析成功且原子数匹配时才处理
                if nat is None or not positions or len(positions) != nat:
                    continue
                
                # 将位置列表转为元组，作为字典的 Key
                struct_key = (nat, tuple(positions))
                outfile = infile + ".out"
                
                if struct_key in structure_db:
                    existing_outfile = structure_db[struct_key]
                    # 建立 .out 文件的链接
                    create_symlink(existing_outfile, outfile, log)
                    total_linked += 1
                    folder_link_count += 1
                else:
                    structure_db[struct_key] = outfile

            print(f"Done. (Linked: {folder_link_count})")

    print(f"\nTotal linked: {total_linked}. See {LOG_FILE} for details.")

if __name__ == "__main__":
    main()