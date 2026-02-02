import os
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from matplotlib.ticker import MaxNLocator

# ================= PRB Style Configuration =================
plt.rcParams.update({
    'font.family': 'serif', 
    'font.serif': ['Times New Roman'],
    'mathtext.fontset': 'stix', 
    'axes.unicode_minus': True,
    'xtick.direction': 'in', 
    'ytick.direction': 'in',
    'xtick.top': True, 
    'ytick.right': True,
    'font.size': 12,
    'axes.labelsize': 14,
    'legend.fontsize': 10,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'lines.linewidth': 1.5,
    'lines.markersize': 6
})

COLORS = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd']
MARKERS = ['o', 's', '^', 'D', 'v']

def load_data(json_path):
    if not os.path.exists(json_path):
        print(f"Error: JSON file '{json_path}' not found.")
        return None
    with open(json_path, 'r') as f:
        return json.load(f)

def plot_convergence(config):
    print("--- Starting Plotting ---")
    
    root_dir = config.get('ROOT_DIR', '.')
    json_name = config.get('OUTPUT_JSON', 'kappa_summary.json')
    json_path = os.path.join(root_dir, json_name)
    
    data = load_data(json_path)
    if not data: return

    organized_data = defaultdict(lambda: defaultdict(dict))
    
    all_grids = sorted(data.keys())
    all_temps = set()
    all_k_indices = set()

    for grid in data:
        for cutoff in data[grid]:
            for temp in data[grid][cutoff]:
                all_temps.add(temp)
                for k_idx in data[grid][cutoff][temp]:
                    all_k_indices.add(k_idx)
    
    sorted_temps = sorted(list(all_temps), key=lambda x: float(x))
    sorted_k_indices = sorted(list(all_k_indices), key=lambda x: int(x))
    
    for temp in sorted_temps:
        for k_idx in sorted_k_indices:
            for grid in all_grids:
                cutoffs = []
                values = []
                
                raw_cutoffs = sorted(data[grid].keys(), key=lambda x: abs(int(x)))
                
                for cut in raw_cutoffs:
                    if temp in data[grid][cut] and k_idx in data[grid][cut][temp]:
                        val = data[grid][cut][temp][k_idx]
                        cutoffs.append(abs(int(cut)))
                        values.append(val)
                
                if cutoffs:
                    organized_data[temp][k_idx][grid] = (cutoffs, values)

    for temp in sorted_temps:
        n_subplots = len(sorted_k_indices)
        
        fig, axes = plt.subplots(1, n_subplots, figsize=(4 * n_subplots, 3.5), squeeze=False)
        axes = axes.flatten()
        
        print(f"Plotting Temperature: {temp} K")
        
        for i, k_idx in enumerate(sorted_k_indices):
            ax = axes[i]
            
            for j, grid in enumerate(all_grids):
                if grid in organized_data[temp][k_idx]:
                    x, y = organized_data[temp][k_idx][grid]
                    
                    color = COLORS[j % len(COLORS)]
                    marker = MARKERS[j % len(MARKERS)]
                    
                    ax.plot(x, y, label=grid, color=color, marker=marker, 
                            linestyle='-', alpha=0.9)
            
            ax.set_xlabel(r'Cutoff Neighbor Index ($N$)')
            
            if i == 0:
                ax.set_ylabel(r'$\kappa$ (W m$^{-1}$ K$^{-1}$)')
            
            direction_map = {'1': 'xx', '5': 'yy', '9': 'zz'}
            dir_label = direction_map.get(k_idx, f"Index {k_idx}")
            ax.set_title(r'$T = {:.0f}$ K, $\kappa_{{{}}}$'.format(float(temp), dir_label))
            
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.legend(frameon=False, loc='best')

        plt.tight_layout()
        
        filename = f"Convergence_{float(temp):.0f}K.png"
        save_path = os.path.join(root_dir, filename)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  [Saved] {save_path}")
        plt.close()

if __name__ == "__main__":
    mock_config = {'ROOT_DIR': '.'}
    if os.path.exists("kappa_summary.json"):
        plot_convergence(mock_config)
    else:
        print("Please run via convergence.py or ensure kappa_summary.json exists.")