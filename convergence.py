#!/usr/bin/env python3
import argparse
import sys
import os

from src.io_utils import ConfigParser
from src import (
    generator, 
    deduplicator, 
    analyzer, 
    qe_runner, 
    fc3_builder,  
    bte_runner,   
    collector,    
    plotter,
    automator       
)

def main():
    parser = argparse.ArgumentParser(
        description="Auto-Thirdorder Workflow Controller",
        usage="python convergence.py [command] [INPUT_FILE]",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    commands_help = (
        "generate    : Generate supercell files (DISP.*)\n"
        "link        : Deduplicate structures using symlinks\n"
        "submit_dft  : Submit DFT (Quantum Espresso) jobs\n"
        "gen_fc3     : Harvest results and generate FORCE_CONSTANTS_3RD\n"
        "analyze     : Analyze computational savings\n"
        "run_bte     : Submit ShengBTE calculation tasks\n"
        "collect     : Collect thermal conductivity results to JSON\n"
        "plot        : Plot convergence curves (PRB style)\n"
        "all         : Run specific sequential steps (use with caution)"
        "auto        : One-click automation (Generate -> Wait -> Plot)\n"
    )
    
    parser.add_argument("command", 
                        choices=['generate', 'link', 'submit_dft', 'gen_fc3', 
                                 'analyze', 'run_bte', 'collect', 'plot', 'all', 'auto'], 
                        help=commands_help)
    
    parser.add_argument("control_file", nargs='?', default="INPUT", 
                        help="Path to configuration file (default: INPUT)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.control_file):
        print(f"Error: Configuration file '{args.control_file}' not found.")
        sys.exit(1)
        
    cfg = ConfigParser(args.control_file)
    
    # =======================================================
    # Step 1: Generate Supercells
    # =======================================================
    if args.command in ['generate', 'all']:
        configs = cfg.get('cell', 'configs')
        base_in = cfg.get('cell', 'base_input')
        tpl_name = cfg.get('cell', 'template_supercell_name')
        thirdorder_bin = cfg.get('cell', 'THIRDORDER_BIN', 'thirdorder_espresso.py')

        if configs and base_in:
            generator.run_generation(configs, base_in, tpl_name, thirdorder_bin)

    # =======================================================
    # Step 2: Link Duplicates
    # =======================================================
    if args.command in ['link', 'all']:
        configs = cfg.get('cell', 'configs')
        if configs:
            deduplicator.run_linking(configs)

    # =======================================================
    # Step 3: Submit DFT Jobs (Quantum Espresso)
    # =======================================================
    if args.command == 'submit_dft':
        dft_cfg = cfg.config.get('dft', {})
        if not dft_cfg:
            print("Error: No &dft section found in INPUT.")
        else:
            qe_runner.submit_dft_jobs(dft_cfg)

    # =======================================================
    # Step 4: Generate Force Constants (Reap)
    # =======================================================
    if args.command == 'gen_fc3':
        configs = cfg.get('cell', 'configs')
        base_in = cfg.get('cell', 'base_input')
        thirdorder_bin = cfg.get('cell', 'THIRDORDER_BIN', 'thirdorder_espresso.py')
        sub_gen_script = cfg.get('cell', 'SUB_GEN_SCRIPT', 'templates/sub_gen.sh')

        if configs and base_in:
            fc3_builder.run_reaping(configs, base_in, thirdorder_bin, sub_gen_script)

    # =======================================================
    # Optional: Analyze Savings
    # =======================================================
    if args.command == 'analyze':
        costs = cfg.get('analyze', 'COST_ESTIMATES')
        if costs:
            analyzer.run_analysis(costs)

    # =======================================================
    # Step 5: Run ShengBTE
    # =======================================================
    if args.command == 'run_bte':
        submit_cfg = cfg.config.get('submit', {})
        if not submit_cfg:
            print("Error: No &submit section found in INPUT.")
        else:
            bte_runner.submit_jobs(submit_cfg)

    # =======================================================
    # Step 6: Collect Results
    # =======================================================
    if args.command in ['collect', 'all']:
        collect_cfg = cfg.config.get('collect', {})
        
        if 'ROOT_DIR' not in collect_cfg:
            collect_cfg['ROOT_DIR'] = cfg.get('submit', 'ROOT_DIR', '.')
        if 'WORK_DIR' not in collect_cfg:
            collect_cfg['WORK_DIR'] = cfg.get('submit', 'WORK_DIR', 'ShengBTE')
            
        collector.run_collection(collect_cfg)

    # =======================================================
    # Step 7: Plot Results
    # =======================================================
    if args.command in ['plot', 'all']:
        plot_cfg = cfg.config.get('collect', {})

        if 'ROOT_DIR' not in plot_cfg:
            plot_cfg['ROOT_DIR'] = cfg.get('submit', 'ROOT_DIR', '.')
            
        plotter.plot_convergence(plot_cfg)

    # =======================================================
    # Automatic One-Click Workflow
    # =======================================================
    if args.command == 'auto':
        automator.run_automation(cfg)
    


if __name__ == "__main__":
    main()