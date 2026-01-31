#!/usr/bin/env python3
import os
import subprocess
import shutil
import sys

# ================= 配置区域 =================
# 格式: (na, nb, nc, cutoff)
# 在这里修改一次即可，Bash 脚本会自动读取
#一次最多提交6个任务，即对应6行，且需要包含已经算过的数据
#截断半径 ($R_{cut}$) 绝对不能超过超胞边界的一半。原理：如果截断半径太长，超过了超胞的一半，原子就会和它自己在周期性边界另一边的“镜像”发生相互作用。这是物理上错误的（Self-interaction artifacts）。
configs = [
    (5, 5, 5, -3),
    (5, 5, 5, -4),
    (5, 5, 5, -5),
    (5, 5, 5, -6),
]
base_input = "si_unit.scf.in"
template_supercell_name = "si_supper.scf.in"
# ===========================================

def run_command(cmd):
    try:
        subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL) # 隐藏常规输出，保持清洁
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running command: {cmd}\n") # 错误输出到 stderr
        sys.exit(1)

def main():
    if not os.path.exists(base_input):
        sys.stderr.write(f"Error: Base input file '{base_input}' not found.\n")
        sys.exit(1)

    generated_folders = []

    for na, nb, nc, cut in configs:
        folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
        generated_folders.append(folder_name)
        
        # 仅当文件夹不存在时才生成，避免重复生成
        if os.path.exists(folder_name):
             # 即使存在也添加到列表，因为后续脚本需要处理它
             continue

        sys.stderr.write(f"--- Generating: {folder_name} ---\n") # 进度信息打印到 stderr
        
        os.makedirs(folder_name)
        
        cmd = f"thirdorder_espresso.py {base_input} sow {na} {nb} {nc} {cut} {template_supercell_name}"
        run_command(cmd)
        
        shutil.copy(base_input, os.path.join(folder_name, base_input))
        
        files_to_move = [f for f in os.listdir('.') if f.startswith("DISP") and (f.endswith(str(na)) or ".in." in f)]
        
        for f in files_to_move:
            if os.path.isfile(f):
                shutil.move(f, os.path.join(folder_name, f))
    
    # === 关键修改：将文件夹列表打印到标准输出 (stdout) ===
    # 这样 Bash 可以通过 $(python generate_cells.py) 捕获这些名字
    for folder in generated_folders:
        print(folder)

if __name__ == "__main__":
    main()