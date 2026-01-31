#!/bin/bash
#SBATCH -p v6_384
#SBATCH -N 1                
#SBATCH -n 96
#SBATCH -J shengBTE_task
#SBATCH -o job.out
#SBATCH -e job.err

source /public1/soft/modules/module.sh
module purge
module load qe/6.7.0-oneAPI.2022.1 

# --- 设置库路径 ---
# 确保这个路径是你自己的真实路径
export LD_LIBRARY_PATH=$HOME/soft/spglib-1.9.9/lib:$LD_LIBRARY_PATH
EXE_PATH=$HOME/soft/sousaw-shengbte-b0d209068239/ShengBTE

# --- 运行检查 ---
if [ ! -f "$EXE_PATH" ]; then
    echo "Error: 找不到程序 $EXE_PATH"
    exit 1
fi

if [ ! -f "CONTROL" ]; then
    echo "Error: 当前目录下没有 CONTROL 文件"
    exit 1
fi

if [ ! -f "espresso.ifc2" ]; then
    echo "Error: 当前目录下没有 espresso.ifc2 文件"
    exit 1
fi

if [ ! -f "FORCE_CONSTANTS_3RD" ]; then
    echo "Error: 当前目录下没有 FORCE_CONSTANTS_3RD 文件"
    exit 1
fi

echo "Starting ShengBTE calculation in $(pwd)..."
mpirun -np 96 $EXE_PATH > shengBTE.log
echo "Job Done."