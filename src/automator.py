import time
import subprocess
import sys
import os
from src import generator, deduplicator, qe_runner, fc3_builder, bte_runner, collector, plotter, analyzer

def check_job_status(job_name_keyword, user):
    try:
        result = subprocess.check_output(f"squeue -u {user}", shell=True).decode('utf-8')
        lines = result.strip().split('\n')
        for line in lines:
            if job_name_keyword in line:
                return True
        return False
    except subprocess.CalledProcessError:
        return False

def wait_for_jobs(step_name, job_keyword, check_interval=300):
    user = subprocess.check_output("whoami", shell=True).decode('utf-8').strip()
    
    print(f"--- [Auto] Waiting for {step_name} jobs ({job_keyword}) to finish... ---")
    
    start_time = time.time()
    while True:
        is_running = check_job_status(job_keyword, user)
        
        if not is_running:
            print(f"--- [Auto] {step_name} jobs finished! Proceeding... ---")
            break
        
        elapsed = (time.time() - start_time) / 3600
        sys.stdout.write(f"\r... Still waiting ({elapsed:.2f} hours elapsed) ...")
        sys.stdout.flush()
        
        time.sleep(check_interval)
    print("")

def verify_fc3_success(configs):
    print("--- [Auto] Verifying FORCE_CONSTANTS_3RD integrity... ---")
    failed_folders = []
    
    for config in configs:
        na, nb, nc, cut = config
        folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
        
        file_path = os.path.join(folder_name, "FORCE_CONSTANTS_3RD")
        
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
            failed_folders.append(folder_name)

    if failed_folders:
        print("\n" + "!"*60)
        print("CRITICAL ERROR: The following folders failed to generate FC3:")
        for f in failed_folders:
            print(f"  - {f}")
        print("!"*60)
        print("Automation stopped to prevent wasted calculation.")
        sys.exit(1)
    
    print("--- [Auto] Verification Passed. All FC3 files are ready. ---")

def verify_shengbte_success(configs, work_dir="ShengBTE"):
    print("--- [Auto] Verifying ShengBTE results (CONV file)... ---")
    failed_folders = []
    target_file = "BTE.KappaTensorVsT_CONV" 
    
    for config in configs:
        na, nb, nc, cut = config
        
        task_folder_name = f"task_{na}{nb}{nc}_{cut}"
        file_path = os.path.join(work_dir, task_folder_name, target_file)
        
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 10:
            failed_folders.append(file_path)

    if failed_folders:
        print("\n" + "!"*60)
        print(f"CRITICAL ERROR: The following files are missing or empty:")
        for f in failed_folders:
            print(f"  - {f}")
        print("!"*60)
        print("Possible reasons:")
        print("1. Job crashed immediately (check output logs in ShengBTE/task_xxx).")
        print("2. Iterative solver failed to converge.")
        sys.exit(1)
    
    print("--- [Auto] Verification Passed. All BTE results are ready. ---")

def run_automation(cfg):
    print("==================================================")
    print("      AUTO-THIRDORDER ONE-CLICK WORKFLOW          ")
    print("==================================================")
    print("Note: Do NOT close this terminal. Use 'nohup' if running remotely.")
    
    print("\n>>> Phase 1: Generation, Analysis & DFT Submission")
    
    configs = cfg.get('cell', 'configs')
    base_in = cfg.get('cell', 'base_input')
    tpl_name = cfg.get('cell', 'template_supercell_name')
    thirdorder_bin = cfg.get('cell', 'THIRDORDER_BIN', 'thirdorder_espresso.py')
    
    generator.run_generation(configs, base_in, tpl_name, thirdorder_bin)
    deduplicator.run_linking(configs)
    
    cost_estimates = cfg.config.get('analyze', {}).get('COST_ESTIMATES', {})
    analyzer.run_analysis(cost_estimates)
    
    dft_cfg = cfg.config.get('dft', {})
    if dft_cfg:
        qe_runner.submit_dft_jobs(dft_cfg)
    else:
        print("Error: No &dft section.")
        return

    wait_for_jobs("DFT Calculation", "scf") 

    print("\n>>> Phase 3: Force Constants Generation")
    
    sub_gen_script = cfg.get('cell', 'SUB_GEN_SCRIPT', 'templates/sub_gen.sh')
    fc3_builder.run_reaping(configs, base_in, thirdorder_bin, sub_gen_script)
    
    wait_for_jobs("FC3 Generation", "Gen_FC3", check_interval=60) 
    
    verify_fc3_success(configs)

    print("\n>>> Phase 4: ShengBTE Calculation")
    
    submit_cfg = cfg.config.get('submit', {})
    if submit_cfg:
        bte_runner.submit_jobs(submit_cfg)
    
    wait_for_jobs("ShengBTE", "ShengBTE", check_interval=60)
    
    bte_work_dir = cfg.get('submit', 'WORK_DIR', 'ShengBTE')
    verify_shengbte_success(configs, work_dir=bte_work_dir)

    print("\n>>> Phase 5: Collection & Plotting")
    
    collect_cfg = cfg.config.get('collect', {})
    if 'ROOT_DIR' not in collect_cfg: collect_cfg['ROOT_DIR'] = cfg.get('submit', 'ROOT_DIR', '.')
    if 'WORK_DIR' not in collect_cfg: collect_cfg['WORK_DIR'] = bte_work_dir
    collector.run_collection(collect_cfg)
    
    print("Data collected. Generating plots...")
    from src import plotter 
    
    plot_cfg = collect_cfg
    if 'ROOT_DIR' not in plot_cfg: plot_cfg['ROOT_DIR'] = cfg.get('submit', 'ROOT_DIR', '.')
    
    plotter.plot_convergence(plot_cfg)

    print("\n==================================================")
    print("          ALL TASKS COMPLETED SUCCESSFULLY        ")
    print("==================================================")