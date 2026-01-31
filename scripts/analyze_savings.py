#!/usr/bin/env python3
import os
import glob
import re
from collections import defaultdict

# ================= 配置区域 =================
# 估算每个超胞大小单次SCF计算的核时 (Core-Hours)
# 估算公式参考: 核心数 x 单个任务平均运行时间 (小时)
# 比如: 333超胞用96核跑了0.5小时 = 48 Core-Hours
COST_ESTIMATES = {
    "333": 50,     # 3x3x3 示例成本
    "444": 150,    # 4x4x4 (原子数是333的2.3倍，DFT计算量通常随原子数立方增长，成本会激增)
    "555": 400,
}
DEFAULT_COST = 100 # 如果字典里没有定义，默认用这个
# ===========================================

def get_folder_info():
    """扫描当前目录下所有的 thirdorder_NaNbNc_Cutoff 文件夹"""
    
    # === 修改点 1: 适配文件夹命名格式 ===
    # 匹配: thirdorder_333_-2 或 thirdorder_444_-3
    # Group 1: 333 (超胞尺寸)
    # Group 2: -2 (截断半径)
    pattern = re.compile(r"thirdorder_(\d{3})_(-?\d+)")
    
    # 数据结构: data[supercell_str][cutoff] = {total, saved}
    data = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'saved': 0}))
    
    # 获取当前目录下匹配的文件夹
    folders = sorted([f for f in os.listdir('.') if os.path.isdir(f) and pattern.match(f)])
    
    for folder in folders:
        match = pattern.match(folder)
        sc_size = match.group(1) # e.g., "333"
        cutoff = match.group(2)  # e.g., "-2"
        
        # === 修改点 2: 适配输入文件查找逻辑 ===
        # 排除 .out 文件，只找 DISP.* 的输入文件
        # 之前脚本生成的是 DISP.si_supper.scf.in.1 这种格式
        input_pattern = os.path.join(folder, "DISP.*")
        all_files = glob.glob(input_pattern)
        
        # 过滤掉以 .out 结尾的文件，剩下的就是输入文件
        input_files = [f for f in all_files if not f.endswith('.out')]
        
        total_count = 0
        saved_count = 0
        
        for inp in input_files:
            total_count += 1
            out_file = inp + ".out"
            
            # === 核心统计逻辑 ===
            # 1. 如果 .out 文件存在 且 是软链接 (Symlink) -> 说明被跳过 (Saved)
            # 2. 如果 .out 文件存在 但 不是链接 -> 说明实际计算了 (Actual Run)
            # 3. 如果 .out 不存在 -> 说明还没算 (Pending)，这里暂归为 Actual Run 的预算中
            if os.path.islink(out_file):
                saved_count += 1
            
        data[sc_size][cutoff]['total'] = total_count
        data[sc_size][cutoff]['saved'] = saved_count
        
    return data

def print_report(data):
    if not data:
        print("No matching folders found.")
        return

    print(f"{'='*85}")
    print(f"{'Supercell':<10} | {'Cutoff':<8} | {'Total Jobs':<10} | {'Linked(Saved)':<14} | {'Actual Run':<10} | {'Savings %':<9}")
    print(f"{'-'*85}")

    grand_total_saved_hours = 0
    grand_total_jobs = 0
    grand_total_saved_jobs = 0
    
    # 对超胞尺寸排序 (333, 444...)
    for sc in sorted(data.keys()):
        sc_total_jobs = 0
        sc_total_saved = 0
        
        # 获取该超胞的单任务成本
        unit_cost = COST_ESTIMATES.get(sc, DEFAULT_COST)
        
        # 按 Cutoff 数值大小排序 (-2, -3, -4)
        # key使用 abs(int(x)) 使得 -2, -3, -4 按 2, 3, 4 排序，或者直接 int(x)
        sorted_cuts = sorted(data[sc].keys(), key=lambda x: int(x), reverse=True) # -2 > -3 > -4
        
        for cut in sorted_cuts:
            stats = data[sc][cut]
            t = stats['total']
            s = stats['saved']
            a = t - s
            pct = (s / t * 100) if t > 0 else 0.0
            
            print(f"{sc:<10} | {cut:<8} | {t:<10} | {s:<14} | {a:<10} | {pct:6.1f}%")
            
            sc_total_jobs += t
            sc_total_saved += s
        
        # --- 该超胞尺寸的汇总 ---
        sc_pct = (sc_total_saved / sc_total_jobs * 100) if sc_total_jobs > 0 else 0.0
        saved_hours = sc_total_saved * unit_cost
        
        grand_total_saved_hours += saved_hours
        grand_total_jobs += sc_total_jobs
        grand_total_saved_jobs += sc_total_saved
        
        print(f"{'-'*85}")
        print(f"SUMMARY {sc} (Cost ~{unit_cost} ch/job):")
        print(f"  - Jobs: {sc_total_jobs} total, {sc_total_saved} saved ({sc_pct:.1f}%)")
        print(f"  - Est. Hours Saved: {saved_hours:,} Core-Hours")
        print(f"{'='*85}\n")

    # 全局汇总
    total_pct = (grand_total_saved_jobs / grand_total_jobs * 100) if grand_total_jobs > 0 else 0.0
    print(f"FINAL REPORT:")
    print(f"  Total Files Checked : {grand_total_jobs}")
    print(f"  Total Files Linked  : {grand_total_saved_jobs}")
    print(f"  Overall Reduction   : {total_pct:.1f}%")
    print(f"  TOTAL EST. SAVINGS  : {grand_total_saved_hours:,} Core-Hours")
    print(f"{'='*85}")

if __name__ == "__main__":
    # 检查是否有相关文件夹
    if not glob.glob("thirdorder_*"):
        print("No 'thirdorder_NxNxN_cutoff' folders found.")
        print("Please ensure you run 'generate_cells.py' and 'link_duplicates.py' first.")
    else:
        results = get_folder_info()
        print_report(results)