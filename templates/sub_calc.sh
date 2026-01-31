#!/bin/bash
#SBATCH -p v6_384
#SBATCH -N 1
#SBATCH -n 96
#SBATCH --array=1-2
#SBATCH -o %A_%a.out

# ================= 配置区域 =================
NUM_CHUNKS=2
# ===========================================

source /public1/soft/modules/module.sh
module purge
module load qe/6.7.0-oneAPI.2022.1

# 1. 获取所有待计算的输入文件 (排除 .out 文件，按数字排序)
files=($(ls DISP.*.in.* | grep -v ".out" | sort -V))

# 2. 计算任务切分逻辑
TOTAL_FILES=${#files[@]}
STEP=$(( (TOTAL_FILES + NUM_CHUNKS - 1) / NUM_CHUNKS ))
START_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) * STEP ))
my_batch=("${files[@]:$START_IDX:$STEP}")

echo "Job Array ID: $SLURM_ARRAY_TASK_ID"
echo "Processing range: from index $START_IDX, count $STEP"
echo "Files in this batch: ${#my_batch[@]}"

# 3. 循环计算当前批次的文件
for input in "${my_batch[@]}"; do
    output="${input}.out"
    
    # --- A. 检查软链接 (跳过) ---
    if [ -L "$output" ]; then
        echo "Skip Linked File: $output -> $(readlink -f $output)"
        continue
    fi

    # --- B. 检查断点续算 (跳过) ---
    if [ -f "$output" ] && grep -q "JOB DONE" "$output"; then
        echo "Skip Completed File: $output"
        continue
    fi
    
    # --- C. 准备计算环境 ---
    
    # 提取文件编号，例如 DISP...in.5 => 5
    file_num=$(echo "$input" | awk -F'.' '{print $NF}')
    
    # 使用绝对路径，防止 QE 找不到
    # $SLURM_SUBMIT_DIR 是你提交任务的目录
    target_outdir="${SLURM_SUBMIT_DIR}/outdir/outdir_${file_num}"
    
    # 确保父目录存在
    mkdir -p "${SLURM_SUBMIT_DIR}/outdir"
    mkdir -p "$target_outdir"
    
    # === [关键修复 1]：自动修复“数字粘连”导致的列数错误 ===
    # 将 "数字-数字" (如 0.123-0.456) 替换为 "数字 -数字" (0.123 -0.456)
    # -i 表示直接修改源文件
    sed -i -E 's/([0-9])(-[0-9])/\1 \2/g' "$input"
    
    # === [关键修复 2]：强制修改输入文件中的 outdir ===
    # 这样 QE 绝对不会去访问错误的目录，而是访问我们刚创建的 target_outdir
    # 使用 | 作为分隔符，防止路径中的 / 冲突
    sed -i "s|outdir.*=.*|outdir = '${target_outdir}'|g" "$input"
    
    echo "Starting calculation: $input (Outdir: $target_outdir)"
    
    # --- D. 运行 QE ---
    # 加上 -input 再次确保 QE 知道读哪个文件
    mpirun -np 96 pw.x -npool 4 -input "$input" > "$output"
    
    # --- E. 清理 ---
    # 只有算完了才删，算错了留着检查（如果你想节省空间，可以取消下面注释）
    rm -rf "$target_outdir"
    
done