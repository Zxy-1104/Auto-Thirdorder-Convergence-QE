#!/usr/bin/env python3
import argparse
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

try:
    from src import config_loader as ConfigParserModule
    ConfigParser = ConfigParserModule.load_config
except ImportError:
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

def resolve_path(relative_path):
    if not relative_path:
        return relative_path
        
    if os.path.isabs(relative_path) or os.path.exists(relative_path):
        return relative_path
    
    global_path = os.path.join(SCRIPT_DIR, relative_path)
    
    if os.path.exists(global_path):
        return global_path
    
    return relative_path

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
        "auto        : One-click automation (Generate -> Wait -> Plot)\n"
    )
    
    parser.add_argument("command", 
                        choices=['generate', 'link', 'submit_dft', 'gen_fc3', 
                                 'analyze', 'run_bte', 'collect', 'plot', 'auto'], 
                        help=commands_help)
    
    parser.add_argument("control_file", nargs='?', default="INPUT", 
                        help="Path to configuration file (default: INPUT)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.control_file):
        print(f"Error: Configuration file '{args.control_file}' not found.")
        sys.exit(1)
        
    raw_cfg = ConfigParser(args.control_file)
    
    def get_cfg_dict(c):
        return c.config if hasattr(c, 'config') else c
    
    cfg_dict = get_cfg_dict(raw_cfg)

    if args.command == 'generate':
        configs = raw_cfg.get('cell', 'configs')
        base_in = raw_cfg.get('cell', 'base_input')
        tpl_name = raw_cfg.get('cell', 'template_supercell_name')
        thirdorder_bin = raw_cfg.get('cell', 'THIRDORDER_BIN', 'thirdorder_espresso.py')

        if configs and base_in:
            generator.run_generation(configs, base_in, tpl_name, thirdorder_bin)

    elif args.command == 'link':
        configs = raw_cfg.get('cell', 'configs')
        if configs:
            deduplicator.run_linking(configs)

    elif args.command == 'analyze':
        analyze_cfg = cfg_dict.get('analyze', {})
        costs = analyze_cfg.get('COST_ESTIMATES')
        if costs:
            analyzer.run_analysis(costs)

    elif args.command == 'submit_dft':
        dft_cfg = cfg_dict.get('dft', {})
        if dft_cfg:
            raw_script = dft_cfg.get('SUB_SCRIPT', 'templates/sub_calc.sh')
            dft_cfg['SUB_SCRIPT'] = resolve_path(raw_script)
            qe_runner.submit_dft_jobs(dft_cfg)
        else:
            print("Error: No &dft section found.")

    elif args.command == 'gen_fc3':
        configs = raw_cfg.get('cell', 'configs')
        base_in = raw_cfg.get('cell', 'base_input')
        thirdorder_bin = raw_cfg.get('cell', 'THIRDORDER_BIN', 'thirdorder_espresso.py')
        
        raw_script = raw_cfg.get('cell', 'SUB_GEN_SCRIPT', 'templates/sub_gen.sh')
        sub_gen_script = resolve_path(raw_script)

        if configs and base_in:
            fc3_builder.run_reaping(configs, base_in, thirdorder_bin, sub_gen_script)

    elif args.command == 'run_bte':
        submit_cfg = cfg_dict.get('submit', {})
        if submit_cfg:
            raw_script = submit_cfg.get('SUB_SCRIPT', 'templates/sub_sheng.sh')
            submit_cfg['SUB_SCRIPT'] = resolve_path(raw_script)
            bte_runner.submit_jobs(submit_cfg)
        else:
            print("Error: No &submit section found.")

    elif args.command == 'collect':
        collect_cfg = cfg_dict.get('collect', {})
        if 'ROOT_DIR' not in collect_cfg:
            collect_cfg['ROOT_DIR'] = raw_cfg.get('submit', 'ROOT_DIR', '.')
        if 'WORK_DIR' not in collect_cfg:
            collect_cfg['WORK_DIR'] = raw_cfg.get('submit', 'WORK_DIR', 'ShengBTE')
            
        collector.run_collection(collect_cfg)

    elif args.command == 'plot':
        collect_cfg = cfg_dict.get('collect', {})
        if 'ROOT_DIR' not in collect_cfg:
            collect_cfg['ROOT_DIR'] = raw_cfg.get('submit', 'ROOT_DIR', '.')
            
        plotter.plot_convergence(collect_cfg)

    elif args.command == 'auto':
        automator.run_automation(raw_cfg)

if __name__ == "__main__":
    main()