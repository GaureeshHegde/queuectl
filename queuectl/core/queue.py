"""
Queue management - core job lifecycle operations
"""
import json
from datetime import datetime, timedelta
from queuectl.core.job import Job, JobState
from queuectl.storage.file_store import FileStore
from queuectl.config import get_config

class JobQueue:
    """Manages job queue operations"""
    
    def __init__(self):
        """Initialize job queue"""
        self.config = get_config()
        self.job_store = FileStore(self.config.get('jobs_dir'))
        self.dlq_store = FileStore(self.config.get('dlq_dir'))
    
    def enqueue(self, job_data):
        """
        Add a job to the queue
        
        Args:
            job_data: Dictionary or JSON string containing job data
            
        Returns:
            Job object
        """
        # Parse job data if it's a JSON string
        if isinstance(job_data, str):
            job_data = json.loads(job_data)
        
        # Extract job parameters
        job_id = job_data.get('id')
        command = job_data.get('command')
        max_retries = job_data.get('max_retries', self.config.get('max_retries'))
        run_at = job_data.get('run_at')  # ADD THIS LINE
        
        if not command:
            raise ValueError("Job must have a 'command' field")
        
        # Create job
        job = Job(
            command=command,
            job_id=job_id,
            max_retries=max_retries,
            state=JobState.PENDING,
            run_at=run_at  # ADD THIS LINE
        )
        
        # Save to storage
        self.job_store.save_job(job)
        
        return job

    
    def get_next_job(self):
        """
        Get next pending job to process
        
        Returns:
            Job object or None if no jobs available
        """
        pending_jobs = self.job_store.list_jobs(state=JobState.PENDING)
        
        # Filter jobs that are ready to run (not waiting for retry)
                # Filter jobs that are ready to run (not waiting for retry or scheduled time)
        now = datetime.utcnow()
        available_jobs = []
        
        for job in pending_jobs:
            # If run_at is set, check if scheduled time has arrived
            if job.run_at:
                run_time = datetime.fromisoformat(job.run_at)
                if run_time > now:
                    continue  # Not scheduled yet
            
            # If next_retry_at is set, check if it's time to retry
            if job.next_retry_at:
                next_retry = datetime.fromisoformat(job.next_retry_at)
                if next_retry > now:
                    continue  # Not ready yet
            
            available_jobs.append(job)

        
        if not available_jobs:
            return None
        
        # Return oldest job (FIFO)
        available_jobs.sort(key=lambda j: j.created_at)
        job = available_jobs[0]
        
        # Mark as processing
        job.update_state(JobState.PROCESSING)
        self.job_store.save_job(job)
        
        return job
    
    def mark_completed(self, job_id):
        """
        Mark job as completed
        
        Args:
            job_id: Job ID to mark as completed
        """
        job = self.job_store.load_job(job_id)
        if job:
            job.update_state(JobState.COMPLETED)
            self.job_store.save_job(job)
    
    def mark_failed(self, job_id, error_message):
        """
        Mark job as failed and handle retry logic
        
        Args:
            job_id: Job ID to mark as failed
            error_message: Error message describing the failure
        """
        job = self.job_store.load_job(job_id)
        if not job:
            return
        
        job.increment_attempts()
        job.update_state(JobState.FAILED, error=error_message)
        
        # Check if should retry
        if job.should_retry():
            # Calculate next retry time with exponential backoff
            backoff_base = self.config.get('backoff_base')
            delay_seconds = backoff_base ** job.attempts
            next_retry = datetime.utcnow() + timedelta(seconds=delay_seconds)
            job.next_retry_at = next_retry.isoformat()
            
            # Move back to pending for retry
            job.update_state(JobState.PENDING)
            self.job_store.save_job(job)
        else:
            # Exhausted retries - move to DLQ
            self.move_to_dlq(job)
    
    def move_to_dlq(self, job):
        """
        Move job to Dead Letter Queue
        
        Args:
            job: Job object to move to DLQ
        """
        job.update_state(JobState.DEAD)
        
        # Save to DLQ
        self.dlq_store.save_job(job)
        
        # Remove from main queue
        self.job_store.delete_job(job.id)
    
    def retry_from_dlq(self, job_id):
        """
        Retry a job from DLQ
        
        Args:
            job_id: Job ID to retry
            
        Returns:
            True if successful, False otherwise
        """
        job = self.dlq_store.load_job(job_id)
        if not job:
            return False
        
        # Reset job state
        job.attempts = 0
        job.error = None
        job.next_retry_at = None
        job.update_state(JobState.PENDING)
        
        # Move back to main queue (save first)
        self.job_store.save_job(job)
        
        # THEN remove from DLQ
        self.dlq_store.delete_job(job_id)
        
        return True

    
    def get_status(self):
        """
        Get queue status summary
        
        Returns:
            Dictionary with job counts by state
        """
        job_counts = self.job_store.count_by_state()
        dlq_count = len(self.dlq_store.list_jobs())
        
        return {
            'jobs': job_counts,
            'dlq_count': dlq_count
        }
    
    def list_jobs(self, state=None):
        """
        List jobs by state
        
        Args:
            state: JobState to filter by (None for all)
            
        Returns:
            List of Job objects
        """
        return self.job_store.list_jobs(state=state)
    
    def list_dlq(self):
        """
        List all jobs in Dead Letter Queue
        
        Returns:
            List of Job objects
        """
        return self.dlq_store.list_jobs()
