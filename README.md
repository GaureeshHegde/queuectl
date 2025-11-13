# QueueCTL - Background Job Queue System

A production-ready CLI-based background job queue system with worker processes, retry mechanism using exponential backoff, Dead Letter Queue (DLQ), and advanced features including job scheduling, output logging, and metrics tracking.

## 🚀 Features

### Mandatory Features
- ✅ **Job Queue Management** - Enqueue and manage background jobs via CLI
- ✅ **Multiple Parallel Workers** - Run multiple worker processes concurrently
- ✅ **Automatic Retries** - Exponential backoff retry mechanism for failed jobs
- ✅ **Dead Letter Queue (DLQ)** - Permanent storage for jobs that exhausted retries
- ✅ **Persistent Storage** - Jobs survive system restarts (file-based with locking)
- ✅ **Configuration Management** - Non-hardcoded, user-configurable settings
- ✅ **Job Timeout** - 5-minute timeout for long-running jobs

### Bonus Features
- 🎁 **Job Output Logging** - Capture STDOUT/STDERR for all jobs
- 🎁 **Scheduled/Delayed Jobs** - Schedule jobs for future execution
- 🎁 **Metrics & Statistics** - Track execution metrics and worker performance
- 🎁 **Comprehensive CLI** - Rich command-line interface with status, logs, and config management

## 📋 Table of Contents

- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Testing](#testing)
- [Project Structure](#project-structure)

## 🏗️ Architecture

### Components

┌─────────────────────────────────────────────────────────┐
│ CLI Layer │
│ (enqueue, worker, status, list, logs, dlq, config) │
└────────────────────┬────────────────────────────────────┘
│
┌────────────────────▼────────────────────────────────────┐
│ Queue Manager │
│ - Job state management │
│ - Retry logic with exponential backoff │
│ - DLQ operations │
└────────────────────┬────────────────────────────────────┘
│
┌────────────────────▼────────────────────────────────────┐
│ Storage Layer │
│ - File-based persistence (JSON) │
│ - File locking (prevents race conditions) │
│ - Atomic operations │
└─────────────────────────────────────────────────────────┘

text
    ┌──────────────┐      ┌──────────────┐
    │  Worker 1    │      │  Worker 2    │  ...
    │  (Process)   │      │  (Process)   │
    └──────────────┘      └──────────────┘
text

### Job Lifecycle

ENQUEUE → PENDING → PROCESSING → COMPLETED
↓
FAILED (retry)
↓
(exponential backoff)
↓
DEAD (moved to DLQ)

text

### Retry Mechanism

Failed jobs are automatically retried with **exponential backoff**:

- **Formula**: `delay = backoff_base ^ attempts` seconds
- **Default**: `backoff_base = 2`, `max_retries = 3`
- **Example timeline**:
  - 1st retry: wait 2¹ = 2 seconds
  - 2nd retry: wait 2² = 4 seconds
  - 3rd retry: wait 2³ = 8 seconds
  - After 3 retries → moved to Dead Letter Queue

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- pip
- Virtual environment (recommended)

### Setup

Clone the repository
git clone <repository-url>
cd queuectl

Create virtual environment
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

Install in development mode
pip install -e .

Verify installation
queuectl --help

text

## 🚀 Quick Start

1. Start workers (3 parallel workers)
queuectl worker start --count 3

2. Enqueue some jobs
queuectl enqueue '{"command":"echo Hello World"}'
queuectl enqueue '{"command":"date"}'
queuectl enqueue '{"command":"sleep 5 && echo Done"}'

3. Check queue status
queuectl status

4. List completed jobs
queuectl list --state completed

5. View job output
queuectl logs <job-id>

6. Stop workers
queuectl worker stop

text

## 📖 Usage Guide

### Job Management

#### Enqueue a Job

Basic job
queuectl enqueue '{"command":"echo test"}'

Job with custom retry settings
queuectl enqueue '{"command":"./my-script.sh", "max_retries": 5}'

Scheduled job (runs after 30 seconds)
queuectl enqueue '{"command":"echo Scheduled"}' --run-at "+30s"

Scheduled job with specific time
queuectl enqueue '{"command":"backup.sh"}' --run-at "2024-01-15T14:30:00"

text

#### List Jobs

List all jobs
queuectl list

Filter by state
queuectl list --state pending
queuectl list --state completed
queuectl list --state failed
queuectl list --state processing

text

#### View Job Output (Bonus Feature)

View logs for a specific job
queuectl logs <job-id>

Example output:
=== Job Output ===
Command: echo Hello World
Return Code: 0
Success: True
=== STDOUT ===
Hello World
=== STDERR ===
text

#### Check Queue Status

queuectl status

Output:
Queue Status:
==================================================
Job Counts by State:
● Pending 5
○ Processing 2
● Completed 150
○ Failed 0
○ Dead 1
Dead Letter Queue: 1 jobs
Active Workers: 3
text

### Worker Management

#### Start Workers

Start single worker
queuectl worker start

Start multiple workers (recommended)
queuectl worker start --count 5

Workers run as separate background processes
text

#### Stop Workers

Stop all workers gracefully
queuectl worker stop

Workers complete current jobs before stopping
text

### Dead Letter Queue (DLQ)

List jobs in DLQ
queuectl dlq list

Retry a specific job from DLQ
queuectl dlq retry <job-id>

Clear entire DLQ
queuectl dlq clear

text

### Configuration Management

Configuration is **NOT hardcoded** and can be modified at runtime:

View current configuration
queuectl config show

Update max retries
queuectl config set max-retries 5

Update backoff base
queuectl config set backoff-base 3

Settings persist to data/config/settings.json
text

### Metrics & Statistics (Bonus Feature)

View execution metrics
queuectl metrics

Output:
Execution Metrics
============================================================
Overall Statistics:
Total Jobs Processed: 150
Completed Successfully: 148
Failed: 2
Success Rate: 98.67%
Failure Rate: 1.33%
Execution Time:
Average per Job: 2.34s
Total Execution Time: 351.23s
Worker Statistics:
worker_1:
Jobs Processed: 50
Completed: 50
Failed: 0
worker_2:
Jobs Processed: 52
Completed: 51
Failed: 1
Reset metrics
queuectl metrics --reset

text

## ⚙️ Configuration

Configuration file: `data/config/settings.json`

{
"max_retries": 3,
"backoff_base": 2,
"worker_poll_interval": 1,
"job_timeout": 300
}

text

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `max_retries` | 3 | Maximum retry attempts before moving to DLQ |
| `backoff_base` | 2 | Base for exponential backoff calculation |
| `worker_poll_interval` | 1 | Worker polling interval (seconds) |
| `job_timeout` | 300 | Job execution timeout (seconds) |

## 🧪 Testing

### Run Comprehensive Test Suite

Run all tests (mandatory + bonus features)
bash test_queuectl.sh

Expected output:
======== MANDATORY FEATURES TEST ========
[PASS] Job enqueueing works
[PASS] Config NOT hardcoded
[PASS] File locking implemented
[PASS] Jobs persist to disk
[PASS] Multiple workers work (3 workers)
[PASS] Retry and DLQ work
======== BONUS FEATURES TEST ========
[PASS] Output logging works (BONUS)
[PASS] Scheduled jobs work (BONUS)
[PASS] Metrics work (BONUS)
======== TEST SUMMARY ========
Total: 9
Passed: 9
Failed: 0
✓ ALL TESTS PASSED!
text

### Manual Testing Examples

Test 1: Parallel execution
queuectl worker start --count 3
queuectl enqueue '{"command":"sleep 5 && echo Job 1"}'
queuectl enqueue '{"command":"sleep 5 && echo Job 2"}'
queuectl enqueue '{"command":"sleep 5 && echo Job 3"}'

All 3 should complete in ~5s, not 15s
Test 2: Retry mechanism
queuectl worker start
queuectl enqueue '{"command":"exit 1"}'

Wait 20s, check DLQ: queuectl dlq list
Test 3: Scheduled jobs
queuectl worker start
queuectl enqueue '{"command":"echo Future"}' --run-at "+10s"

Job won't execute immediately
Test 4: Persistence
queuectl enqueue '{"command":"echo test"}'

Restart terminal/system
queuectl list --state pending # Job still exists

queuectl worker stop

text

## 📁 Project Structure

queuectl/
├── queuectl/
│ ├── init.py
│ ├── cli/
│ │ ├── init.py
│ │ ├── parser.py # CLI argument parsing
│ │ └── commands.py # Command handlers
│ ├── core/
│ │ ├── init.py
│ │ ├── job.py # Job model and states
│ │ ├── queue.py # Queue management logic
│ │ └── worker.py # Worker process implementation
│ ├── storage/
│ │ ├── init.py
│ │ └── file_store.py # File-based persistence with locking
│ └── metrics.py # Metrics tracking (bonus feature)
├── data/
│ ├── jobs/ # Job state files (*.json)
│ ├── dlq/ # Dead letter queue
│ ├── logs/ # Job output logs (bonus feature)
│ ├── config/ # Configuration files
│ └── workers/ # Worker PID files
├── setup.py # Package configuration
├── README.md # This file
├── test_queuectl.sh # Comprehensive test script
└── .gitignore

text

## 🔒 Thread Safety & Race Conditions

The system uses **file-based locking** (via `filelock` library) to prevent race conditions:

- ✅ Multiple workers can safely read/write jobs
- ✅ Atomic job state transitions
- ✅ No job processed twice
- ✅ Safe concurrent enqueue operations

## 🎯 Design Decisions

1. **File-based Storage**: Simple, portable, survives restarts
2. **Separate Worker Processes**: True parallelism, isolation, easy monitoring
3. **Exponential Backoff**: Prevents overwhelming failed services
4. **DLQ Pattern**: Industry-standard approach for failed jobs
5. **CLI-first**: Simple deployment, no web server required

## 🐛 Troubleshooting

### Workers not processing jobs

Check if workers are running
ps aux | grep queuectl.core.worker

Check worker logs
queuectl status

Restart workers
queuectl worker stop
queuectl worker start

text

### Jobs stuck in pending state

Check if scheduled time has passed (for scheduled jobs)
queuectl list --state pending

Start workers if none running
queuectl worker start

text

### Configuration not persisting

Verify config file exists and is writable
cat data/config/settings.json

Re-apply configuration
queuectl config set max-retries 3

text

## 📝 License

This project is created as part of a technical assessment.

## 👤 Author

Gaureesh

---