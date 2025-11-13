"""
Command handlers for queuectl CLI
"""
import json
import os
import signal
import subprocess
import sys
from queuectl.core.queue import JobQueue
from queuectl.core.job import JobState
from queuectl.config import get_config

def handle_enqueue(args):
    """Handle enqueue command"""
    try:
        from datetime import datetime, timedelta
        import json
        
        queue = JobQueue()
        
        # Parse job data
        if isinstance(args.job_data, str):
            job_data = json.loads(args.job_data)
        else:
            job_data = args.job_data
        
        # Handle --run-at flag
        if hasattr(args, 'run_at') and args.run_at:
            run_at_str = args.run_at
            
            # Support relative time format like "+30s", "+5m", "+1h"
            if run_at_str.startswith('+'):
                # Parse relative time
                value = int(run_at_str[1:-1])
                unit = run_at_str[-1]
                
                if unit == 's':
                    delta = timedelta(seconds=value)
                elif unit == 'm':
                    delta = timedelta(minutes=value)
                elif unit == 'h':
                    delta = timedelta(hours=value)
                else:
                    raise ValueError(f"Unknown time unit: {unit}. Use 's', 'm', or 'h'")
                
                run_at = datetime.utcnow() + delta
                job_data['run_at'] = run_at.isoformat()
            else:
                # Assume ISO format
                job_data['run_at'] = run_at_str
        
        job = queue.enqueue(job_data)
        
        print(f"✓ Job enqueued successfully")
        print(f"  ID: {job.id}")
        print(f"  Command: {job.command}")
        print(f"  State: {job.state.value}")
        if job.run_at:
            print(f"  Scheduled for: {job.run_at}")
    except Exception as e:
        print(f"✗ Error enqueueing job: {e}")
        sys.exit(1)


def handle_worker_start(args):
    """Handle worker start command"""
    try:
        worker_count = args.count
        print(f"Starting {worker_count} worker(s)...")
        
        # Store PIDs for tracking
        pid_file = "data/config/worker_pids.txt"
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)
        
        pids = []
        for i in range(1, worker_count + 1):
            # Start worker as background process
            process = subprocess.Popen(
                [sys.executable, "-m", "queuectl.core.worker", str(i)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            pids.append(str(process.pid))
            print(f"  Worker {i} started (PID: {process.pid})")
        
        # Save PIDs
        with open(pid_file, 'w') as f:
            f.write('\n'.join(pids))
        
        print(f"✓ {worker_count} worker(s) started successfully")
        print(f"  Use 'queuectl worker stop' to stop them")
        
    except Exception as e:
        print(f"✗ Error starting workers: {e}")
        sys.exit(1)

def handle_worker_stop(args):
    """Handle worker stop command"""
    try:
        pid_file = "data/config/worker_pids.txt"
        
        if not os.path.exists(pid_file):
            print("No running workers found")
            return
        
        with open(pid_file, 'r') as f:
            pids = [line.strip() for line in f if line.strip()]
        
        if not pids:
            print("No running workers found")
            return
        
        print(f"Stopping {len(pids)} worker(s)...")
        
        for pid_str in pids:
            try:
                pid = int(pid_str)
                os.kill(pid, signal.SIGTERM)
                print(f"  Sent stop signal to worker (PID: {pid})")
            except ProcessLookupError:
                print(f"  Worker (PID: {pid}) already stopped")
            except Exception as e:
                print(f"  Error stopping worker (PID: {pid}): {e}")
        
        # Remove PID file
        os.remove(pid_file)
        print("✓ All workers stopped")
        
    except Exception as e:
        print(f"✗ Error stopping workers: {e}")
        sys.exit(1)

def handle_status(args):
    """Handle status command"""
    try:
        queue = JobQueue()
        status = queue.get_status()
        
        print("Queue Status:")
        print("=" * 50)
        print("\nJob Counts by State:")
        for state, count in status['jobs'].items():
            icon = "●" if count > 0 else "○"
            print(f"  {icon} {state.capitalize():12} {count:>5}")
        
        print(f"\nDead Letter Queue: {status['dlq_count']} jobs")
        
        # Check for running workers
        pid_file = "data/config/worker_pids.txt"
        active_workers = 0
        
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                for pid_str in f:
                    try:
                        pid = int(pid_str.strip())
                        os.kill(pid, 0)  # Check if process exists
                        active_workers += 1
                    except (ProcessLookupError, ValueError):
                        pass
        
        print(f"Active Workers:    {active_workers}")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Error getting status: {e}")
        sys.exit(1)

def handle_list(args):
    """Handle list command"""
    try:
        queue = JobQueue()
        
        # Convert state string to JobState enum if provided
        state_filter = None
        if args.state:
            state_filter = JobState(args.state)
        
        jobs = queue.list_jobs(state=state_filter)
        
        if not jobs:
            state_msg = f" with state '{args.state}'" if args.state else ""
            print(f"No jobs found{state_msg}")
            return
        
        print(f"Jobs ({len(jobs)} total):")
        print("=" * 80)
        
        for job in jobs:
            print(f"\nID:       {job.id}")
            print(f"Command:  {job.command}")
            print(f"State:    {job.state.value}")
            print(f"Attempts: {job.attempts}/{job.max_retries}")
            print(f"Created:  {job.created_at}")
            if job.error:
                print(f"Error:    {job.error}")
            print("-" * 80)
        
    except Exception as e:
        print(f"✗ Error listing jobs: {e}")
        sys.exit(1)


def handle_logs(args):
    """Handle logs command"""
    try:
        import os
        log_file = f"data/logs/{args.job_id}.log"
        
        if not os.path.exists(log_file):
            print(f"✗ No logs found for job {args.job_id}")
            print(f"  Job may not have been executed yet or logs directory doesn't exist")
            sys.exit(1)
        
        with open(log_file, 'r') as f:
            content = f.read()
            print(content)
        
    except Exception as e:
        print(f"✗ Error reading logs: {e}")
        sys.exit(1)



def handle_dlq_list(args):
    """Handle DLQ list command"""
    try:
        queue = JobQueue()
        dlq_jobs = queue.list_dlq()
        
        if not dlq_jobs:
            print("Dead Letter Queue is empty")
            return
        
        print(f"Dead Letter Queue ({len(dlq_jobs)} jobs):")
        print("=" * 80)
        
        for job in dlq_jobs:
            print(f"\nID:       {job.id}")
            print(f"Command:  {job.command}")
            print(f"Attempts: {job.attempts}")
            print(f"Error:    {job.error}")
            print(f"Failed:   {job.updated_at}")
            print("-" * 80)
        
    except Exception as e:
        print(f"✗ Error listing DLQ: {e}")
        sys.exit(1)

def handle_dlq_retry(args):
    """Handle DLQ retry command"""
    try:
        queue = JobQueue()
        success = queue.retry_from_dlq(args.job_id)
        
        if success:
            print(f"✓ Job {args.job_id} moved back to queue for retry")
        else:
            print(f"✗ Job {args.job_id} not found in Dead Letter Queue")
            sys.exit(1)
        
    except Exception as e:
        print(f"✗ Error retrying job: {e}")
        sys.exit(1)

def handle_config_set(args):
    """Handle config set command"""
    try:
        config = get_config()
        
        # Validate key
        valid_keys = ['max-retries', 'backoff-base']
        if args.key not in valid_keys:
            print(f"✗ Invalid config key: {args.key}")
            print(f"  Valid keys: {', '.join(valid_keys)}")
            sys.exit(1)
        
        # Convert hyphenated key to underscore
        key = args.key.replace('-', '_')
        
        config.set(key, args.value)
        print(f"✓ Configuration updated: {args.key} = {args.value}")
        
    except ValueError as e:
        print(f"✗ Invalid value: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error setting config: {e}")
        sys.exit(1)

def handle_config_show(args):
    """Handle config show command"""
    try:
        config = get_config()
        settings = config.get_all()
        
        print("Current Configuration:")
        print("=" * 50)
        print(f"  max-retries:  {settings['max_retries']}")
        print(f"  backoff-base: {settings['backoff_base']}")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Error showing config: {e}")
        sys.exit(1)

def execute_command(args):
    """Route parsed arguments to appropriate handler"""
    if args.command == 'enqueue':
        handle_enqueue(args)
    
    elif args.command == 'worker':
        if args.worker_command == 'start':
            handle_worker_start(args)
        elif args.worker_command == 'stop':
            handle_worker_stop(args)
    
    elif args.command == 'status':
        handle_status(args)
    
    elif args.command == 'list':
        handle_list(args)
    
    elif args.command == 'logs':  
        handle_logs(args)

    elif args.command == 'dlq':
        if args.dlq_command == 'list':
            handle_dlq_list(args)
        elif args.dlq_command == 'retry':
            handle_dlq_retry(args)
    
    elif args.command == 'config':
        if args.config_command == 'set':
            handle_config_set(args)
        elif args.config_command == 'show':
            handle_config_show(args)
    
    elif args.command == 'metrics':  
        handle_metrics(args)

    else:
        print(f"Unknown command: {args.command}")

def handle_metrics(args):
    """Handle metrics command"""
    try:
        from queuectl.metrics import get_metrics_tracker
        
        metrics_tracker = get_metrics_tracker()
        
        if args.reset:
            metrics_tracker.reset_metrics()
            print("✓ Metrics reset successfully")
            return
        
        metrics = metrics_tracker.get_metrics()
        
        print("Execution Metrics")
        print("=" * 60)
        print(f"\nOverall Statistics:")
        print(f"  Total Jobs Processed:    {metrics['total_jobs']}")
        print(f"  Completed Successfully:  {metrics['completed_jobs']}")
        print(f"  Failed:                  {metrics['failed_jobs']}")
        print(f"  Success Rate:            {metrics['success_rate']}%")
        print(f"  Failure Rate:            {metrics['failure_rate']}%")
        
        print(f"\nExecution Time:")
        print(f"  Average per Job:         {metrics['avg_execution_time']:.2f}s")
        print(f"  Total Execution Time:    {metrics['total_execution_time']:.2f}s")
        
        if metrics['worker_stats']:
            print(f"\nWorker Statistics:")
            for worker, stats in metrics['worker_stats'].items():
                print(f"  {worker}:")
                print(f"    Jobs Processed:  {stats['jobs_processed']}")
                print(f"    Completed:       {stats['jobs_completed']}")
                print(f"    Failed:          {stats['jobs_failed']}")
        
        print(f"\nLast Updated: {metrics['last_updated']}")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error displaying metrics: {e}")
        sys.exit(1)
