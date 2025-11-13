"""
Metrics tracking for job queue system
"""
import json
import os
from datetime import datetime
from threading import Lock

class MetricsTracker:
    """Tracks execution metrics for the job queue"""
    
    def __init__(self, metrics_file='data/metrics.json'):
        """Initialize metrics tracker"""
        self.metrics_file = metrics_file
        self.lock = Lock()
        self._ensure_metrics_file()
    
    def _ensure_metrics_file(self):
        """Ensure metrics file exists with default structure"""
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        
        if not os.path.exists(self.metrics_file):
            default_metrics = {
                'total_jobs': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'total_execution_time': 0.0,
                'worker_stats': {},
                'last_updated': datetime.utcnow().isoformat()
            }
            self._save_metrics(default_metrics)
    
    def _load_metrics(self):
        """Load metrics from file"""
        with self.lock:
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {
                    'total_jobs': 0,
                    'completed_jobs': 0,
                    'failed_jobs': 0,
                    'total_execution_time': 0.0,
                    'worker_stats': {},
                    'last_updated': datetime.utcnow().isoformat()
                }
    
    def _save_metrics(self, metrics):
        """Save metrics to file"""
        with self.lock:
            metrics['last_updated'] = datetime.utcnow().isoformat()
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
    
    def record_job_start(self, job_id, worker_id):
        """Record when a job starts processing"""
        metrics = self._load_metrics()
        
        # Initialize worker stats if needed
        worker_key = f"worker_{worker_id}"
        if worker_key not in metrics['worker_stats']:
            metrics['worker_stats'][worker_key] = {
                'jobs_processed': 0,
                'jobs_completed': 0,
                'jobs_failed': 0
            }
        
        metrics['total_jobs'] += 1
        metrics['worker_stats'][worker_key]['jobs_processed'] += 1
        
        self._save_metrics(metrics)
    
    def record_job_completion(self, job_id, worker_id, execution_time, success):
        """
        Record job completion
        
        Args:
            job_id: Job identifier
            worker_id: Worker identifier
            execution_time: Time taken to execute (seconds)
            success: Whether job succeeded
        """
        metrics = self._load_metrics()
        
        worker_key = f"worker_{worker_id}"
        
        if success:
            metrics['completed_jobs'] += 1
            metrics['worker_stats'][worker_key]['jobs_completed'] += 1
        else:
            metrics['failed_jobs'] += 1
            metrics['worker_stats'][worker_key]['jobs_failed'] += 1
        
        metrics['total_execution_time'] += execution_time
        
        self._save_metrics(metrics)
    
    def get_metrics(self):
        """Get current metrics"""
        metrics = self._load_metrics()
        
        # Calculate derived metrics
        total = metrics['total_jobs']
        completed = metrics['completed_jobs']
        failed = metrics['failed_jobs']
        
        if total > 0:
            success_rate = (completed / total) * 100
            failure_rate = (failed / total) * 100
        else:
            success_rate = 0.0
            failure_rate = 0.0
        
        if completed > 0:
            avg_execution_time = metrics['total_execution_time'] / completed
        else:
            avg_execution_time = 0.0
        
        return {
            'total_jobs': total,
            'completed_jobs': completed,
            'failed_jobs': failed,
            'success_rate': round(success_rate, 2),
            'failure_rate': round(failure_rate, 2),
            'avg_execution_time': round(avg_execution_time, 2),
            'total_execution_time': round(metrics['total_execution_time'], 2),
            'worker_stats': metrics['worker_stats'],
            'last_updated': metrics['last_updated']
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        default_metrics = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_execution_time': 0.0,
            'worker_stats': {},
            'last_updated': datetime.utcnow().isoformat()
        }
        self._save_metrics(default_metrics)

# Global metrics instance
_metrics = None

def get_metrics_tracker():
    """Get global metrics tracker instance"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsTracker()
    return _metrics
