"""
Job model and state management
"""
import uuid
from datetime import datetime
from enum import Enum

class JobState(Enum):
    """Job states"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"

class Job:
    """Represents a background job"""
    
    def __init__(self, command, job_id=None, state=JobState.PENDING, 
             attempts=0, max_retries=3, created_at=None, updated_at=None,
             error=None, next_retry_at=None, output_file=None, run_at=None):

        """
        Initialize a job
        
        Args:
            command: Shell command to execute
            job_id: Unique job identifier (auto-generated if not provided)
            state: Current job state
            attempts: Number of execution attempts
            max_retries: Maximum retry attempts before moving to DLQ
            created_at: Creation timestamp
            updated_at: Last update timestamp
            error: Last error message (if any)
            next_retry_at: Timestamp for next retry attempt
        """
        self.id = job_id or str(uuid.uuid4())
        self.command = command
        self.state = state if isinstance(state, JobState) else JobState(state)
        self.attempts = attempts
        self.max_retries = max_retries
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()
        self.error = error
        self.next_retry_at = next_retry_at
        self.output_file = output_file
        self.run_at = run_at
    
    def to_dict(self):
        """Convert job to dictionary for serialization"""
        return {
            'id': self.id,
            'command': self.command,
            'state': self.state.value,
            'attempts': self.attempts,
            'max_retries': self.max_retries,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'error': self.error,
            'next_retry_at': self.next_retry_at,
            'output_file': self.output_file,
            'run_at': self.run_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create job from dictionary"""
        return cls(
            command=data['command'],
            job_id=data.get('id'),
            state=data.get('state', 'pending'),
            attempts=data.get('attempts', 0),
            max_retries=data.get('max_retries', 3),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            error=data.get('error'),
            next_retry_at=data.get('next_retry_at'),
            output_file=data.get('output_file'),
            run_at=data.get('run_at')
        )
    
    def update_state(self, new_state, error=None):
        """Update job state and timestamp"""
        self.state = new_state if isinstance(new_state, JobState) else JobState(new_state)
        self.updated_at = datetime.utcnow().isoformat()
        if error:
            self.error = error
    
    def increment_attempts(self):
        """Increment attempt counter"""
        self.attempts += 1
        self.updated_at = datetime.utcnow().isoformat()
    
    def should_retry(self):
        """Check if job should be retried"""
        return self.attempts < self.max_retries
    
    def __repr__(self):
        return f"Job(id={self.id}, command={self.command}, state={self.state.value}, attempts={self.attempts})"
