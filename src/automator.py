import time
import subprocess
import sys
import os
from src import generator, deduplicator, qe_runner, fc3_builder, bte_runner, collector, plotter, analyzer

def resolve_path(relative_path):
    if not relative_path: return relative_path
    if os.path.isabs(relative_path) or os.path.exists(relative_path):
        return relative_path
    
    install_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    global_path = os.path.join(install_dir, relative_path)
    
    if os.path.exists(global_path):
        return global_path
    return relative_path

def check_job_status(job_name_keyword, user):
    try:
        result = subprocess.check_output(f"squeue -u {user}", shell=True).decode('utf-8')
        return any(job_name_keyword in line for line in result.split('\n'))
    except subprocess.CalledProcessError:
        return False

def wait_for_jobs(step_name, job_keyword, check_interval=300):
    user = subprocess.check_output("whoami", shell=True).decode('utf-8').strip()
    print(f"--- [Auto] Waiting for {step_name} jobs ({job_keyword}) to finish... ---")
    
    start_time = time.time()
    while True:
        if not check_job_status(job_keyword, user):
            print(f"--- [Auto] {step_name} jobs finished! Proceeding... ---")
            break
        
        elapsed = (time.time() - start_time) / 3600
        sys.stdout.write(f"\r... Still waiting ({elapsed:.2f} hours elapsed) ...")
        sys.stdout.flush()
        time.sleep(check_interval)
    print("")

def verify_fc3_success(configs):
    print("--- [Auto] Verifying FORCE_CONSTANTS_3RD integrity... ---")
    failed = []
    for config in configs:
        na, nb, nc, cut = config
        fpath = os.path.join(f"thirdorder_{na}{nb}{nc}_{cut}", "FORCE_CONSTANTS_3RD")
        if not os.path.exists(fpath) or os.path.getsize(fpath) < 100:
            failed.append(fpath)
            
    if failed:
        print("\nCRITICAL ERROR: FC3 generation failed for:")
        for f in failed: print(f"  - {f}")
        sys.exit(1)
    print("--- [Auto] Verification Passed. ---")

def verify_shengbte_success(configs, work_dir="ShengBTE"):
    print("--- [Auto] Verifying ShengBTE results... ---")
    failed = []
    target = "BTE.KappaTensorVsT_CONV"
    for config in configs:
        na, nb, nc, cut = config
        fpath = os.path.join(work_dir, f"task_{na}{nb}{nc}_{cut}", target)
        if not os.path.exists(fpath) or os.path.getsize(fpath) < 10:
            failed.append(fpath)

    if failed:
        print(f"\nCRITICAL ERROR: Missing {target} for:")
        for f in failed: print(f"  - {f}")
        sys.exit(1)
    print("--- [Auto] Verification Passed. ---")

def run_automation(cfg):
    print("==================================================")
    print("      AUTO-THIRDORDER ONE-CLICK WORKFLOW          ")
    print("==================================================")
    
    def get_cfg_dict(c): return c.config if hasattr(c, 'config') else c
    cfg_dict = get_cfg_dict(cfg)

    print("\n>>> Phase 1: Generation & DFT")
    configs = cfg.get('cell', 'configs')
    base_in = cfg.get('cell', 'base_input')
    tpl_name = cfg.get('cell', 'template_supercell_name')
    thirdorder_bin = cfg.get('cell', 'THIRDORDER_BIN', 'thirdorder_espresso.py')
    
    generator.run_generation(configs, base_in, tpl_name, thirdorder_bin)
    deduplicator.run_linking(configs)
    
    analyzer.run_analysis(cfg_dict.get('analyze', {}).get('COST_ESTIMATES', {}))
    
    dft_cfg = cfg_dict.get('dft', {})
    if dft_cfg:
        dft_cfg['SUB_SCRIPT'] = resolve_path(dft_cfg.get('SUB_SCRIPT', 'templates/sub_calc.sh'))
        qe_runner.submit_dft_jobs(dft_cfg)
    else:
        print("Error: No &dft section.")
        return

    wait_for_jobs("DFT Calculation", "scf") 

    print("\n>>> Phase 3: FC3 Generation")
    raw_gen = cfg.get('cell', 'SUB_GEN_SCRIPT', 'templates/sub_gen.sh')
    sub_gen_script = resolve_path(raw_gen)
    
    fc3_builder.run_reaping(configs, base_in, thirdorder_bin, sub_gen_script)
    wait_for_jobs("FC3 Generation", "Gen_FC3", check_interval=60) 
    verify_fc3_success(configs)

    print("\n>>> Phase 4: ShengBTE")
    submit_cfg = cfg_dict.get('submit', {})
    if submit_cfg:
        submit_cfg['SUB_SCRIPT'] = resolve_path(submit_cfg.get('SUB_SCRIPT', 'templates/sub_sheng.sh'))
        bte_runner.submit_jobs(submit_cfg)
    
    wait_for_jobs("ShengBTE", "ShengBTE", check_interval=60)
    
    bte_work_dir = cfg.get('submit', 'WORK_DIR', 'ShengBTE')
    verify_shengbte_success(configs, work_dir=bte_work_dir)

    print("\n>>> Phase 5: Collection & Plotting")
    collect_cfg = cfg_dict.get('collect', {})
    if 'ROOT_DIR' not in collect_cfg: collect_cfg['ROOT_DIR'] = cfg.get('submit', 'ROOT_DIR', '.')
    if 'WORK_DIR' not in collect_cfg: collect_cfg['WORK_DIR'] = bte_work_dir
    
    collector.run_collection(collect_cfg)
    plotter.plot_convergence(collect_cfg)

    print("\n==================================================")
    print("          ALL TASKS COMPLETED SUCCESSFULLY        ")
    print("==================================================")