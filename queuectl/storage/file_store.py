"""
File-based storage with locking for job persistence
"""
import json
import os
from filelock import FileLock
from queuectl.core.job import Job

class FileStore:
    """Handles persistent storage of jobs using JSON files"""
    
    def __init__(self, storage_dir):
        """
        Initialize file store
        
        Args:
            storage_dir: Directory to store job files
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_job_path(self, job_id):
        """Get file path for a job"""
        return os.path.join(self.storage_dir, f"{job_id}.json")
    
    def _get_lock_path(self, job_id):
        """Get lock file path for a job"""
        return os.path.join(self.storage_dir, f"{job_id}.lock")
    
    def save_job(self, job):
        """
        Save job to disk with file locking
        
        Args:
            job: Job object to save
        """
        job_path = self._get_job_path(job.id)
        lock_path = self._get_lock_path(job.id)
        
        with FileLock(lock_path, timeout=10):
            with open(job_path, 'w') as f:
                json.dump(job.to_dict(), f, indent=2)
    
    def load_job(self, job_id):
        """
        Load job from disk with file locking
        
        Args:
            job_id: Job ID to load
            
        Returns:
            Job object or None if not found
        """
        job_path = self._get_job_path(job_id)
        lock_path = self._get_lock_path(job_id)
        
        if not os.path.exists(job_path):
            return None
        
        with FileLock(lock_path, timeout=10):
            with open(job_path, 'r') as f:
                data = json.load(f)
                return Job.from_dict(data)
    
    def delete_job(self, job_id):
        """
        Delete job from disk
        
        Args:
            job_id: Job ID to delete
        """
        job_path = self._get_job_path(job_id)
        lock_path = self._get_lock_path(job_id)
        
        # Remove job file
        if os.path.exists(job_path):
            with FileLock(lock_path, timeout=10):
                os.remove(job_path)
        
        # Remove lock file
        if os.path.exists(lock_path):
            os.remove(lock_path)
    
    def list_jobs(self, state=None):
        """
        List all jobs, optionally filtered by state
        
        Args:
            state: JobState to filter by (None for all jobs)
            
        Returns:
            List of Job objects
        """
        jobs = []
        
        if not os.path.exists(self.storage_dir):
            return jobs
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                job_id = filename[:-5]  # Remove .json extension
                job = self.load_job(job_id)
                
                if job:
                    if state is None or job.state == state:
                        jobs.append(job)
        
        return jobs
    
    def count_by_state(self):
        """
        Count jobs by state
        
        Returns:
            Dictionary mapping state to count
        """
        from queuectl.core.job import JobState
        
        counts = {state: 0 for state in JobState}
        
        if not os.path.exists(self.storage_dir):
            return {state.value: 0 for state in JobState}
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                job_id = filename[:-5]
                job = self.load_job(job_id)
                if job:
                    counts[job.state] += 1
        
        return {state.value: count for state, count in counts.items()}
