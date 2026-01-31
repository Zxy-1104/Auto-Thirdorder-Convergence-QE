#!/bin/bash

# 加载环境
source ~/.bashrc
source ~/anaconda3/bin/activate base

# 1. 生成超胞
# 只要 configs 里保留了旧配置，python 脚本会跳过已存在的文件夹，只生成新的
echo "Step 1: Generating Supercells..."
FOLDERS_STR=$(python3 generate_cells.py)
readarray -t FOLDERS <<< "$FOLDERS_STR"

if [ ${#FOLDERS[@]} -eq 0 ]; then
    echo "Error: No folders generated."
    exit 1
fi

# 2. 链接重复结构
# 这一步必须保留全量 configs，因为新文件夹(-4)需要去链接旧文件夹(-2)的文件
echo "Step 2: Linking Duplicates..."
python3 link_duplicates.py

PREV_JOB_ID=""

# 3. 循环提交计算任务
echo "Step 3: Submitting Calculation Jobs..."

for folder in "${FOLDERS[@]}"; do
    if [ -z "$folder" ]; then continue; fi
    cd "$folder" || exit
    
    # ================= 智能跳过逻辑 (新增) =================
    
    # A. 检查是否已经彻底算完了 (reap 任务已完成)
    if [ -f "reap.out" ] && grep -q "JOB DONE" "reap.out"; then
        echo "✅ [SKIP] $folder: Already finished (reap.out found)."
        # 即使跳过，也要获取它的 JobID 吗？
        # 如果前面算完了，后面新的任务依赖它吗？
        # 通常不同超胞大小之间没有Slurm依赖，只有同文件夹内的 calc->reap 依赖。
        # 所以直接 continue 即可。
        cd ..
        continue
    fi

    # B. 检查是否正在运行 (查询 squeue)
    # 我们用 grep 匹配文件夹名，因为之前的脚本把文件夹名设为了 Job Name 的一部分 (reap_thirdorder_...)
    # 或者我们检查是否有属于当前用户的任务在该目录下运行
    # 这里使用最简单的名字匹配法
    IS_RUNNING=$(squeue -u $USER -o "%.200j" | grep "$folder")
    if [ -n "$IS_RUNNING" ]; then
        echo "⏳ [SKIP] $folder: Jobs are currently running in queue."
        cd ..
        continue
    fi
    
    # ======================================================

    echo "🚀 Submitting new jobs for $folder..."
    
    num_files=$(ls DISP.*.in.* | grep -v ".out" | wc -l)
    if [ "$num_files" -eq 0 ]; then
        echo "No files to calculate in $folder"
        cd ..
        continue
    fi
    
    cp ../sub_calc.sh .
    
    # 提交计算任务 (Array)
    # 注意：这里去掉了 dependency PREV_JOB_ID，
    # 因为不同超胞大小(如 333 和 444)通常可以并行算，不需要等待上一个算完。
    # 如果你确实需要严格顺序执行（为了省节点），可以把下面这行取消注释
    # DEP_ARG="--dependency=afterok:$PREV_JOB_ID"
    
    JOB_ID=$(sbatch --parsable --array=1-2 sub_calc.sh)
    echo "  -> Batch Job ID: $JOB_ID"
    
    PREV_JOB_ID=$JOB_ID
    
    # 提交 Reap 任务
    params=$(echo $folder | sed 's/thirdorder_//; s/_/ /g' | awk '{print substr($1,1,1), substr($1,2,1), substr($1,3,1), $2}')
    
    # 注意：为了让上面的 squeue check 生效，我们将 Job Name 设置为包含 folder 名字
    sbatch --dependency=afterok:$JOB_ID \
           -p v6_384 -N 1 -n 1 -J "reap_$folder" -o reap.out \
           --wrap="source ~/anaconda3/bin/activate base; \
                   find . -name 'DISP.*.out' | sort -V | \
                   thirdorder_espresso.py si_unit.scf.in reap $params; \
                   conda deactivate"
    
    cd ..
done

echo "Done."

