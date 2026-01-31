#!/usr/bin/env python3
import os
import glob
import re
import json
import numpy as np
from collections import defaultdict

# ================= 配置区域 =================
TEMPERATURE = 300.0  # 目标温度 (K)
TARGET_FILE = "BTE.KappaTensorVsT_CONV" # 目标文件名
OUTPUT_JSON = "kappa_summary.json"      # 结果保存文件名
# ===========================================

def get_kappa_from_conv(filepath, target_temp):
    """
    从 BTE.KappaTensorVsT_CONV 读取特定温度的 Kappa_xx (第二列)
    文件格式示例:
      300.0   0.399E+02   ...
    """
    if not os.path.exists(filepath):
        return None
    
    try:
        # 使用 numpy 读取数据，处理科学计数法更稳健
        data = np.loadtxt(filepath)
        
        # 处理只有一行数据的情况 (变成1维数组)
        if data.ndim == 1:
            data = data.reshape(1, -1)
            
        # 遍历每一行寻找对应的温度
        for row in data:
            T = row[0]
            if abs(T - target_temp) < 0.1: # 允许 0.1K 的误差
                # 取第二列 (Index 1) 作为热导率
                return float(row[1])
                
    except Exception as e:
        # print(f"Error reading {filepath}: {e}")
        return None
    
    return None

def main():
    # 数据结构: results[sc_size][cutoff] = kappa
    results = defaultdict(dict)
    
    # 扫描 task_* 文件夹
    pattern = re.compile(r"task_(\d{3})_(-?\d+)")
    task_folders = glob.glob("task_*")
    
    print(f"Scanning {len(task_folders)} task folders for {TARGET_FILE}...")
    
    for folder in task_folders:
        match = pattern.match(folder)
        if not match: continue
        
        sc_raw = match.group(1)      # "333"
        cutoff = int(match.group(2)) # -2 (int)
        
        # 格式化超胞名字: "333" -> "3x3x3" (绘图时好看)
        sc_label = f"{sc_raw[0]}x{sc_raw[1]}x{sc_raw[2]}"
        
        target_path = os.path.join(folder, TARGET_FILE)
        val = get_kappa_from_conv(target_path, TEMPERATURE)
        
        if val is not None:
            results[sc_label][cutoff] = val
        else:
            print(f"  [WARN] Data missing or invalid in {folder}")

    # === 1. 打印表格到终端 ===
    sorted_sc = sorted(results.keys())
    for sc in sorted_sc:
        print(f"\nGrid: {sc}")
        print(f"{'Cutoff':<10} {'Kappa (W/mK)':<20}")
        print("-" * 30)
        
        # 按截断距离的绝对值排序 (2, 3, 4...)
        cutoffs = sorted(results[sc].keys(), key=lambda x: abs(x))
        for cut in cutoffs:
            val = results[sc][cut]
            print(f"{cut:<10} {val:.5E}")

    # === 2. 保存数据供绘图使用 ===
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\n[Success] Results saved to {OUTPUT_JSON} (ready for plotting)")

if __name__ == "__main__":
    main()