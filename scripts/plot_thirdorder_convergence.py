import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import ScalarFormatter, MaxNLocator  # 导入刻度定位器

# --- 配置 Matplotlib 样式 ---
matplotlib.rcParams['axes.unicode_minus'] = True
# matplotlib.rcParams["font.family"] = ["SimHei"] # 如果需要中文标签请取消注释
matplotlib.rcParams['xtick.direction'] = 'in'
matplotlib.rcParams['ytick.direction'] = 'in'

# --- 1. 配置路径 (只需修改这里) ---
data_dir = r"D:\QE脚本\QE_output\Si"
save_root = r"D:\QE脚本\QE_picture"
json_filename = "kappa_summary.json"

# 定义文件的完整路径
data_file = os.path.join(data_dir, json_filename)
material_name = os.path.basename(data_dir)  # 自动提取材料名 (Si)


def plot_convergence():
    # 检查数据文件是否存在
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found. Please run collect_results.py first.")
        return

    # 读取数据
    with open(data_file, 'r') as f:
        results = json.load(f)

    if not results:
        print("Error: No data in JSON file.")
        return

    # --- 3. 绘图 ---
    # 使用参考脚本的画布尺寸
    fig, ax = plt.subplots(figsize=(7, 5.5))

    # 定义样式循环 (颜色和标记)
    colors = ['#D62728', '#1F77B4', '#2CA02C', '#FF7F0E']  # 红, 蓝, 绿, 橙
    markers = ['o', 's', '^', 'D']

    # 获取排序后的超胞列表 (3x3x3, 4x4x4)
    sc_list = sorted(results.keys())

    for idx, sc in enumerate(sc_list):
        data_map = results[sc]

        # 提取 x (cutoff) 和 y (kappa)
        # 按照 cutoff 的绝对值排序，保证连线正确
        sorted_cuts = sorted(data_map.keys(), key=lambda x: abs(int(x)))

        x_vals = [int(k) for k in sorted_cuts]
        y_vals = [data_map[k] for k in sorted_cuts]

        # 转换 x 为绝对值用于绘图 (物理含义：第几近邻)
        plot_x = [abs(x) for x in x_vals]

        color = colors[idx % len(colors)]
        marker = markers[idx % len(markers)]

        ax.plot(plot_x, y_vals,
                color=color, linestyle='-', linewidth=2,
                marker=marker, markersize=8, markerfacecolor=color, markeredgecolor='white', markeredgewidth=1.5,
                label=f'Supercell {sc}')

    # --- 格式化坐标轴 ---
    # 设置 Y 轴格式 (使用 ScalarFormatter)
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((-2, 2))  # 超过范围自动转科学计数法
    ax.yaxis.set_major_formatter(formatter)

    # 设置 X 轴为整数刻度 (MaxNLocator)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # 标签与标题 (参考参考脚本的字体大小)
    ax.set_xlabel('Neighbor Shell Cutoff (N)', fontsize=18)
    ax.set_ylabel(r'$\kappa_{lat}$ ($W \cdot m^{-1} \cdot K^{-1}$)', fontsize=18)
    ax.set_title(f'{material_name} 3rd-Order Convergence', fontsize=20)

    # 网格与刻度 (参考参考脚本的样式)
    ax.grid(True, which="both", linestyle=':', alpha=0.6)
    ax.tick_params(axis='both', which='both', labelsize=16, length=6)

    # 图例 (参考参考脚本，无边框)
    ax.legend(fontsize=14, frameon=False)

    plt.tight_layout()

    # --- 4. 自动保存 ---
    # 完全保留参考脚本的保存逻辑
    save_dir = os.path.join(save_root, material_name)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已自动创建文件夹：{save_dir}")

    save_file = os.path.join(save_dir, f"{material_name}_Convergence_Kappa.png")
    plt.savefig(save_file, dpi=300)
    plt.show()
    plt.close()
    print(f"图片已保存至：{save_file}")


if __name__ == "__main__":
    plot_convergence()