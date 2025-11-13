# QueueCTL - Background Job Queue System

A CLI-based background job queue system with worker processes, retry mechanism using exponential backoff, and Dead Letter Queue (DLQ).

## Features

### Mandatory Features
- Job queue management via CLI
- Multiple parallel workers
- Automatic retry with exponential backoff
- Dead Letter Queue (DLQ) for failed jobs
- Persistent storage with file locking
- Configurable settings (non-hardcoded)

### Bonus Features
- Job output logging (capture STDOUT/STDERR)
- Scheduled/delayed jobs
- Metrics and execution statistics
- Job timeout (5 minutes)

## Installation

Clone repository
git clone https://github.com/GaureeshHegde/queuectl.git
cd queuectl

Create virtual environment
python3 -m venv venv
source venv/bin/activate

Install
pip install -e .

Verify
queuectl --help


## Quick Start

Start workers
queuectl worker start --count 3

Enqueue jobs
queuectl enqueue '{"command":"echo Hello World"}'
queuectl enqueue '{"command":"date"}'

Check status
queuectl status

List jobs
queuectl list --state completed

View logs
queuectl logs <job-id>

Stop workers
queuectl worker stop


## Usage

### Job Management

**Enqueue a job:**
queuectl enqueue '{"command":"echo test"}'


**Schedule a job:**
queuectl enqueue '{"command":"backup.sh"}' --run-at "+30s"
queuectl enqueue '{"command":"backup.sh"}' --run-at "2024-01-15T14:30:00"


**List jobs:**
queuectl list
queuectl list --state pending
queuectl list --state completed


**View job output:**
queuectl logs <job-id>


**Check queue status:**
queuectl status


### Worker Management

**Start workers:**
queuectl worker start # Single worker
queuectl worker start --count 5 # Multiple workers


**Stop workers:**
queuectl worker stop


### Dead Letter Queue

**List DLQ jobs:**
queuectl dlq list


**Retry a job from DLQ:**
queuectl dlq retry <job-id>


**Clear DLQ:**
queuectl dlq clear


### Configuration

Configuration is stored in `data/config/settings.json` and can be modified:

queuectl config show
queuectl config set max-retries 5
queuectl config set backoff-base 3


**Configuration options:**
- `max_retries`: Maximum retry attempts (default: 3)
- `backoff_base`: Base for exponential backoff (default: 2)
- `worker_poll_interval`: Worker polling interval in seconds (default: 1)
- `job_timeout`: Job execution timeout in seconds (default: 300)

### Metrics

View execution statistics:

queuectl metrics
queuectl metrics --reset


## Retry Mechanism

Failed jobs are retried with exponential backoff:
- Formula: `delay = backoff_base ^ attempts` seconds
- Example with default settings (base=2, max_retries=3):
  - 1st retry: wait 2 seconds
  - 2nd retry: wait 4 seconds
  - 3rd retry: wait 8 seconds
  - After 3 retries: moved to DLQ

## Testing

Run the comprehensive test suite:

bash test_queuectl.sh


The test script verifies:
- All mandatory features
- Bonus features
- Concurrent execution
- Retry mechanism
- Configuration persistence
- File locking

## Project Structure

queuectl/
├── queuectl/
│ ├── cli/ # CLI interface
│ ├── core/ # Job, queue, and worker logic
│ ├── storage/ # File-based persistence
│ └── metrics.py # Metrics tracking
├── data/
│ ├── jobs/ # Job state files
│ ├── dlq/ # Dead letter queue
│ ├── logs/ # Job output logs
│ └── config/ # Configuration
├── setup.py
├── README.md
└── test_queuectl.sh


## How It Works

1. Jobs are enqueued and stored as JSON files in `data/jobs/`
2. Workers poll the queue and process pending jobs
3. Failed jobs are retried with exponential backoff
4. Jobs that exhaust retries are moved to DLQ
5. File locking prevents race conditions between workers
6. Job output is captured in `data/logs/`

## Requirements

- Python 3.7+
- filelock library (for thread-safe operations)

## License

Created as part of a technical assessment.

## Author

Gaureesh Hegde