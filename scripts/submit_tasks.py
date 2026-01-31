#!/usr/bin/env python3
import os
import glob
import re
import shutil
import subprocess

# ================= 配置 =================
# 根目录 (相对于当前脚本的位置)
ROOT_DIR = ".." 
# 模板文件
CONTROL_FILE = "CONTROL"
IFC2_FILE = "espresso.ifc2"
SUB_SCRIPT = "sub_sheng.sh"

# [新增] 检查的目标结果文件
TARGET_RESULT = "BTE.KappaTensorVsT_CONV"
# =======================================

def run_cmd(cmd):
    subprocess.call(cmd, shell=True)

def main():
    # 1. 扫描上级目录寻找 thirdorder_* 文件夹
    # 匹配模式: thirdorder_333_-2
    pattern = re.compile(r"thirdorder_(\d{3})_(-?\d+)")
    
    source_folders = sorted(glob.glob(os.path.join(ROOT_DIR, "thirdorder_*")))
    
    print(f"Found {len(source_folders)} source folders.")

    skipped_count = 0
    submitted_count = 0

    for src_folder in source_folders:
        folder_name = os.path.basename(src_folder)
        match = pattern.match(folder_name)
        
        if not match:
            continue

        sc_size = match.group(1) # e.g. 333
        cutoff = match.group(2)  # e.g. -2
        
        # 定义任务文件夹名称
        task_dir = f"task_{sc_size}_{cutoff}"

        # =======================================================
        # [新增核心逻辑] 检查是否已计算完成
        # =======================================================
        result_path = os.path.join(task_dir, TARGET_RESULT)
        
        # 判断条件：
        # 1. 文件夹存在
        # 2. 结果文件存在
        # 3. 结果文件大小大于 0 (防止空文件)
        if os.path.exists(task_dir) and os.path.exists(result_path) and os.path.getsize(result_path) > 0:
            print(f"✅ [SKIP] {task_dir}: Result '{TARGET_RESULT}' already exists.")
            skipped_count += 1
            continue
        # =======================================================

        # 检查源文件夹里是否有三阶力常数
        fc3_path = os.path.join(src_folder, "FORCE_CONSTANTS_3RD")
        if not os.path.exists(fc3_path):
            print(f"⚠️ [WARN] No FORCE_CONSTANTS_3RD in {folder_name}, skipping.")
            continue

        # 2. 创建或更新当前目录下的任务文件夹
        if not os.path.exists(task_dir):
            os.makedirs(task_dir)
            print(f"Creating task directory: {task_dir}")
        else:
            # 如果文件夹存在但没有结果文件，说明可能上次算挂了或者没交上去
            # 我们选择更新文件并重新提交
            print(f"Updating task directory: {task_dir} (Result missing)")

        # 3. 准备文件 (复制/链接)
        
        # A. 复制 CONTROL
        shutil.copy(CONTROL_FILE, os.path.join(task_dir, "CONTROL"))
        
        # B. 链接 espresso.ifc2
        dest_ifc2 = os.path.join(task_dir, "espresso.ifc2")
        if not os.path.exists(dest_ifc2):
            os.symlink(os.path.abspath(IFC2_FILE), dest_ifc2)
            
        # C. 链接 FORCE_CONSTANTS_3RD
        dest_fc3 = os.path.join(task_dir, "FORCE_CONSTANTS_3RD")
        # 如果链接已存在或是一个损坏的链接，先删除
        if os.path.exists(dest_fc3) or os.path.islink(dest_fc3):
            os.remove(dest_fc3) 
        os.symlink(os.path.abspath(fc3_path), dest_fc3)
        
        # D. 复制提交脚本
        shutil.copy(SUB_SCRIPT, os.path.join(task_dir, SUB_SCRIPT))

        # 4. 提交任务
        os.chdir(task_dir)
        
        # [可选] 进阶检查：检查是否已经有正在运行的任务
        # 如果你刚才运行了一遍脚本，结果文件还没生成，不希望立刻重复提交
        # 可以通过 squeue 检查作业名。
        # 这里为了简单，仅使用“结果文件是否存在”作为判断依据。
        
        job_name = f"K_{sc_size}_{cutoff}"
        print(f"🚀 Submitting job for {folder_name}...")
        
        cmd = f"sbatch -J {job_name} {SUB_SCRIPT}"
        subprocess.call(cmd, shell=True)
        submitted_count += 1
        
        os.chdir("..") # 返回上一级

    print(f"\nTotal Summary:")
    print(f"  Skipped (Done): {skipped_count}")
    print(f"  Submitted     : {submitted_count}")

if __name__ == "__main__":
    if not os.path.exists(IFC2_FILE):
        print("Error: espresso.ifc2 not found in current directory.")
    else:
        main()