"""
Worker process - executes jobs from the queue
"""
import subprocess
import time
import signal
import sys
from queuectl.core.queue import JobQueue
from queuectl.core.job import JobState
from queuectl.metrics import get_metrics_tracker

class Worker:
    """Worker process that executes jobs"""
    
    def __init__(self, worker_id=1):
        """
        Initialize worker
        
        Args:
            worker_id: Unique worker identifier
        """
        self.worker_id = worker_id
        self.queue = JobQueue()
        self.running = False
        self.current_job = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n[Worker {self.worker_id}] Received shutdown signal. Finishing current job...")
        self.running = False
    
    def execute_command(self, command, output_file=None):
        """
        Execute a shell command and optionally save output to file
        
        Args:
            command: Shell command to execute
            output_file: Path to save output (optional)
            
        Returns:
            Tuple of (success: bool, output: str, error: str)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            
            # Save output to file if specified
            if output_file:
                import os
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w') as f:
                    f.write(f"=== Job Output ===\n")
                    f.write(f"Command: {command}\n")
                    f.write(f"Return Code: {result.returncode}\n")
                    f.write(f"Success: {success}\n\n")
                    f.write(f"=== STDOUT ===\n{stdout}\n\n")
                    f.write(f"=== STDERR ===\n{stderr}\n")
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 300 seconds"
        except Exception as e:
            return False, "", str(e)

    
    def process_job(self, job):
        """
        Process a single job
        
        Args:
            job: Job object to process
        """
        import time
        
        self.current_job = job
        metrics = get_metrics_tracker()
        
        print(f"[Worker {self.worker_id}] Processing job {job.id}: {job.command}")
        
        # Record job start
        metrics.record_job_start(job.id, self.worker_id)
        
        # Create output file path
        output_file = f"data/logs/{job.id}.log"
        job.output_file = output_file
        
        # Time the execution
        start_time = time.time()
        
        # Execute command with output logging
        success, stdout, stderr = self.execute_command(job.command, output_file)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Record completion
        metrics.record_job_completion(job.id, self.worker_id, execution_time, success)
        
        if success:
            print(f"[Worker {self.worker_id}] ✓ Job {job.id} completed successfully in {execution_time:.2f}s")
            self.queue.mark_completed(job.id)
        else:
            error_msg = stderr or "Command failed"
            print(f"[Worker {self.worker_id}] ✗ Job {job.id} failed: {error_msg}")
            self.queue.mark_failed(job.id, error_msg)
        
        self.current_job = None


    
    def run(self, poll_interval=2):
        """
        Main worker loop
        
        Args:
            poll_interval: Seconds to wait between checking for new jobs
        """
        self.running = True
        print(f"[Worker {self.worker_id}] Started. Polling for jobs...")
        
        while self.running:
            try:
                # Get next job
                job = self.queue.get_next_job()
                
                if job:
                    self.process_job(job)
                else:
                    # No jobs available, wait before checking again
                    time.sleep(poll_interval)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[Worker {self.worker_id}] Error: {e}")
                time.sleep(poll_interval)
        
        print(f"[Worker {self.worker_id}] Stopped gracefully")

def start_worker(worker_id=1):
    """
    Start a worker process
    
    Args:
        worker_id: Unique worker identifier
    """
    worker = Worker(worker_id=worker_id)
    worker.run()

if __name__ == '__main__':
    # Allow running worker directly
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    start_worker(worker_id)
