import time
import subprocess
import sys
import os
import glob
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
        cmd = f"squeue -u {user} -o '%.100j' -h"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        return any(job_name_keyword in line for line in result.split('\n') if line.strip())
    except subprocess.CalledProcessError:
        return False

def wait_for_jobs(step_name, job_keyword, check_interval=300):
    user = subprocess.check_output("whoami", shell=True).decode('utf-8').strip()
    print(f"--- [Auto] Waiting for {step_name} jobs (Keyword: '{job_keyword}') to finish... ---")
    
    start_time = time.time()
    while True:
        if not check_job_status(job_keyword, user):
            print(f"--- [Auto] {step_name} jobs finished in queue. ---")
            break
        
        elapsed = (time.time() - start_time) / 60 
        sys.stdout.write(f"\r    ... Still waiting ({elapsed:.1f} min elapsed) ...")
        sys.stdout.flush()
        time.sleep(check_interval)
    print("")

def check_log_completion(folder, specific_log_name, pattern_log_name, success_key, failure_key=None):
    if specific_log_name:
        specific_path = os.path.join(folder, specific_log_name)
        if os.path.exists(specific_path):
            try:
                with open(specific_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if success_key in content:
                        return True
                    if failure_key and failure_key in content:
                        raise RuntimeError(f"Job failed in {folder}. Check log: {specific_log_name}")
            except RuntimeError:
                raise
            except Exception:
                pass
            return False

    files = glob.glob(os.path.join(folder, pattern_log_name))
    if not files:
        return False
        
    latest_log = max(files, key=os.path.getmtime)
    try:
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if success_key in content:
                return True
            if failure_key and failure_key in content:
                raise RuntimeError(f"Job failed in {folder}. Check log: {os.path.basename(latest_log)}")
    except RuntimeError:
        raise
    except Exception:
        pass
        
    return False

def ensure_dft_files_ready(configs, check_interval=60):
    print("--- [Auto] Verifying DFT output file availability (I/O Sync Check) ---")
    
    while True:
        all_ready = True
        waiting_list = []

        for config in configs:
            na, nb, nc, cut = config
            folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
            
            if not os.path.exists(folder_name):
                continue

            inputs = glob.glob(os.path.join(folder_name, "DISP.*"))
            valid_inputs = [f for f in inputs if not f.endswith(('.out', '.in', '.save', '.xml', '.run'))]
            expected_count = len(valid_inputs)

            if expected_count == 0:
                continue

            outputs = glob.glob(os.path.join(folder_name, "DISP.*.out"))
            actual_count = len(outputs)

            if actual_count < expected_count:
                all_ready = False
                waiting_list.append(f"{folder_name} ({actual_count}/{expected_count})")
        
        if all_ready:
            print("--- [Auto] All DFT output files are verified on disk. Proceeding. ---")
            break
        else:
            print(f"    ... Waiting for filesystem sync: {', '.join(waiting_list[:3])} ...")
            time.sleep(check_interval)

def ensure_fc3_finished(configs, check_interval=30):
    print("--- [Auto] Verifying FC3 Generation logs (Keyword: 'Success') ---")
    
    while True:
        all_done = True
        pending_list = []
        
        for config in configs:
            na, nb, nc, cut = config
            folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
            
            try:
                is_done = check_log_completion(folder_name, "reap.out", "slurm-*.out", "Success", "Error: Generation failed")
                if not is_done:
                    all_done = False
                    pending_list.append(folder_name)
            except RuntimeError as e:
                print(f"\n[CRITICAL ERROR] {e}")
                sys.exit(1)

        if all_done:
            print("--- [Auto] All FC3 jobs confirmed success. ---")
            print("    ... Buffering 30s for safety ...")
            time.sleep(30)
            break
        else:
            print(f"    ... Waiting for logs to update: {', '.join(pending_list[:3])} ...")
            time.sleep(check_interval)

def ensure_shengbte_finished(configs, work_dir, check_interval=30):
    print("--- [Auto] Verifying ShengBTE logs (Keyword: 'Job Done') ---")
    
    while True:
        all_done = True
        pending_list = []
        
        for config in configs:
            na, nb, nc, cut = config
            folder_name = f"task_{na}{nb}{nc}_{cut}"
            task_path = os.path.join(work_dir, folder_name)
            
            if not os.path.exists(task_path): 
                continue
                
            try:
                is_done = check_log_completion(task_path, "shengbte.out", "slurm-*.out", "Job Done", "Job Failed")
                if not is_done:
                    all_done = False
                    pending_list.append(folder_name)
            except RuntimeError as e:
                print(f"\n[CRITICAL ERROR] {e}")
                sys.exit(1)

        if all_done:
            print("--- [Auto] All ShengBTE jobs confirmed success. ---")
            print("    ... Buffering 30s for safety ...")
            time.sleep(30)
            break
        else:
            print(f"    ... Waiting for logs to update: {', '.join(pending_list[:3])} ...")
            time.sleep(check_interval)

def verify_fc3_success(configs):
    print("--- [Auto] Verifying FORCE_CONSTANTS_3RD integrity... ---")
    failed = []
    for config in configs:
        na, nb, nc, cut = config
        folder_name = f"thirdorder_{na}{nb}{nc}_{cut}"
        fpath = os.path.join(folder_name, "FORCE_CONSTANTS_3RD")
        
        if not os.path.exists(fpath) or os.path.getsize(fpath) < 100:
            failed.append(folder_name)
            
    if failed:
        print("\n[CRITICAL ERROR] FC3 generation failed for the following folders:")
        for f in failed: print(f"  - {f}")
        print("Please check the error logs inside these folders.")
        sys.exit(1)
    print("--- [Auto] Verification Passed. ---")

def verify_shengbte_success(configs, work_dir="ShengBTE"):
    print("--- [Auto] Verifying ShengBTE results... ---")
    failed = []
    target = "BTE.KappaTensorVsT_CONV"
    for config in configs:
        na, nb, nc, cut = config
        folder_name = f"task_{na}{nb}{nc}_{cut}"
        fpath = os.path.join(work_dir, folder_name, target)
        
        if not os.path.exists(fpath) or os.path.getsize(fpath) < 10:
            failed.append(folder_name)

    if failed:
        print(f"\n[CRITICAL ERROR] Missing {target} for:")
        for f in failed: print(f"  - {f}")
        sys.exit(1)
    print("--- [Auto] Verification Passed. ---")

def run_automation(cfg):
    print("==================================================")
    print("      AUTO-THIRDORDER ONE-CLICK WORKFLOW          ")
    print("==================================================")
    
    def get_cfg_dict(c): return c.config if hasattr(c, 'config') else c
    cfg_dict = get_cfg_dict(cfg)

    print("\n>>> Phase 1: Generation & Deduplication")
    configs = cfg.get('cell', 'configs')
    base_in = cfg.get('cell', 'base_input')
    tpl_name = cfg.get('cell', 'template_supercell_name')
    thirdorder_bin = cfg.get('cell', 'THIRDORDER_BIN', 'thirdorder_espresso.py')
    
    generator.run_generation(configs, base_in, tpl_name, thirdorder_bin)
    deduplicator.run_linking(configs)

    analyze_conf = cfg_dict.get('analyze', {}).copy()
    if 'COST_ESTIMATES' in cfg_dict:
        analyze_conf['COST_ESTIMATES'] = cfg_dict['COST_ESTIMATES']
    analyzer.run_analysis(analyze_conf)
    
    print("\n>>> Phase 2: DFT Submission")
    dft_cfg = cfg_dict.get('dft', {})
    if dft_cfg:
        raw_script = dft_cfg.get('SUB_SCRIPT', 'templates/sub_calc.sh')
        dft_cfg['SUB_SCRIPT'] = resolve_path(raw_script)
        qe_runner.submit_dft_jobs(dft_cfg)
    else:
        print("Error: No &dft section.")
        return

    wait_for_jobs("DFT Calculation", "scf_array", check_interval=300)

    ensure_dft_files_ready(configs)

    print("\n>>> Phase 3: FC3 Generation")
    
    raw_script = cfg.get('cell', 'SUB_GEN_SCRIPT', 'templates/sub_gen.sh')
    sub_gen_script = resolve_path(raw_script)

    fc3_builder.run_reaping(cfg, sub_gen_script)
    
    wait_for_jobs("FC3 Generation", "Gen_FC3", check_interval=120)
    
    ensure_fc3_finished(configs)
    
    verify_fc3_success(configs)

    print("\n>>> Phase 4: ShengBTE Calculation")
    submit_cfg = cfg_dict.get('submit', {})
    if submit_cfg:
        raw_script = submit_cfg.get('SUB_SCRIPT', 'templates/sub_sheng.sh')
        submit_cfg['SUB_SCRIPT'] = resolve_path(raw_script)
        bte_runner.submit_jobs(submit_cfg)
    
    wait_for_jobs("ShengBTE", "shengBTE", check_interval=120)
    
    bte_work_dir = cfg.get('submit', 'WORK_DIR', 'ShengBTE')
    
    ensure_shengbte_finished(configs, bte_work_dir)
    
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