# QueueCTL - Background Job Queue System

A production-ready CLI-based background job queue system with worker processes, automatic retry mechanism, and comprehensive job management features.

## Table of Contents
- [Features](#features)
- [Setup Instructions](#setup-instructions)
- [Usage Examples](#usage-examples)
- [Architecture Overview](#architecture-overview)
- [Assumptions & Trade-offs](#assumptions--trade-offs)
- [Testing Instructions](#testing-instructions)
- [Project Structure](#project-structure)

## Features

### Mandatory Features
- **Job Queue Management** - Enqueue jobs via CLI and track their lifecycle through pending, processing, completed, and failed states
- **Multiple Parallel Workers** - Run multiple worker processes concurrently to process jobs in parallel for improved throughput
- **Automatic Retry with Exponential Backoff** - Failed jobs are automatically retried with increasing delays (2s, 4s, 8s...) to prevent overwhelming failing services
- **Dead Letter Queue (DLQ)** - Jobs that exhaust all retry attempts are moved to DLQ for manual inspection and retry
- **Persistent Storage** - All jobs are stored as JSON files with atomic operations and survive system restarts. File locking prevents race conditions between workers
- **Configurable Settings** - All settings (retry count, backoff rate, timeout) are stored in JSON config files and can be modified at runtime without code changes

### Bonus Features
- **Job Output Logging** - Capture and store STDOUT/STDERR for all executed jobs for debugging and auditing
- **Scheduled/Delayed Jobs** - Schedule jobs for future execution with absolute or relative timestamps
- **Metrics & Statistics** - Track execution metrics including success rates, execution times, and per-worker statistics
- **Job Timeout** - Automatic termination of jobs exceeding 5-minute execution limit

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- pip package manager
- Virtual environment (recommended)

### Installation Steps

1. Clone the repository
git clone https://github.com/GaureeshHegde/queuectl.git
cd queuectl

2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install dependencies and package
pip install -e .

4. Verify installation
queuectl --help


The installation creates the following directory structure:
data/
├── jobs/ # Job state files
├── dlq/ # Dead letter queue
├── logs/ # Job output logs
├── config/ # Configuration files
└── workers/ # Worker PID files


## Usage Examples

### Basic Job Queue Operations

**Enqueue a simple job:**
$ queuectl enqueue '{"command":"echo Hello World"}'
✓ Job enqueued successfully
ID: a1b2c3d4-5e6f-7890-abcd-ef1234567890
Command: echo Hello World
State: pending


**Start workers to process jobs:**
$ queuectl worker start --count 3
Starting 3 worker(s)...
Worker 1 started (PID: 12345)
Worker 2 started (PID: 12346)
Worker 3 started (PID: 12347)
✓ 3 worker(s) started successfully


**Check queue status:**
$ queuectl status
Queue Status:
Job Counts by State:
● Pending 5
○ Processing 2
● Completed 150
○ Failed 0
○ Dead 1

Dead Letter Queue: 1 jobs
Active Workers: 3


**List jobs by state:**
$ queuectl list --state completed
Jobs (150 total):
ID: a1b2c3d4-5e6f-7890-abcd-ef1234567890
Command: echo Hello World
State: completed
Attempts: 0/3
Created: 2024-01-15T10:30:00.123456


**View job output logs:**
$ queuectl logs a1b2c3d4-5e6f-7890-abcd-ef1234567890
=== Job Output ===
Command: echo Hello World
Return Code: 0
Success: True

=== STDOUT ===
Hello World

=== STDERR ===


### Advanced Features

**Schedule a delayed job:**
Run after 30 seconds
$ queuectl enqueue '{"command":"backup.sh"}' --run-at "+30s"

Run at specific time
$ queuectl enqueue '{"command":"report.py"}' --run-at "2024-01-15T14:30:00"


**View execution metrics:**
$ queuectl metrics
Execution Metrics
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


**Dead Letter Queue operations:**
List failed jobs in DLQ
$ queuectl dlq list

Retry a specific job
$ queuectl dlq retry <job-id>

Clear entire DLQ
$ queuectl dlq clear


**Configuration management:**
View current settings
$ queuectl config show
Configuration:
max_retries: 3
backoff_base: 2
worker_poll_interval: 1
job_timeout: 300

Update configuration
$ queuectl config set max-retries 5
✓ Configuration updated: max-retries = 5


## Architecture Overview

### System Components

┌─────────────┐
│ CLI │ (User Interface)
└──────┬──────┘
│
┌──────▼──────┐
│ Queue │ (Job Management & State Transitions)
│ Manager │ - Enqueue/Dequeue operations
└──────┬──────┘ - Retry logic with exponential backoff
│ - DLQ management
┌──────▼──────┐
│ Storage │ (Persistence Layer)
│ Layer │ - File-based JSON storage
└─────────────┘ - File locking (race condition prevention)
- Atomic operations

   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │Worker 1 │  │Worker 2 │  │Worker 3 │
   └─────────┘  └─────────┘  └─────────┘
   (Separate processes polling and executing jobs)

### Job Lifecycle

1. **PENDING** → Job is enqueued and waiting to be processed
2. **PROCESSING** → Worker picks up job and begins execution
3. **COMPLETED** → Job executes successfully
4. **FAILED** → Job fails, enters retry cycle with exponential backoff
5. **DEAD** → Job exhausts all retries, moved to Dead Letter Queue

### Retry Mechanism

Failed jobs are retried using exponential backoff:
- **Formula:** `delay = backoff_base ^ attempt_number`
- **Default configuration:** base=2, max_retries=3
- **Example timeline:**
  - Initial execution: Immediate
  - 1st retry: 2¹ = 2 seconds wait
  - 2nd retry: 2² = 4 seconds wait
  - 3rd retry: 2³ = 8 seconds wait
  - After 3 retries: Moved to DLQ

### Data Persistence

**Storage Strategy:**
- Each job is stored as a separate JSON file: `data/jobs/{job_id}.json`
- File locking (using `filelock` library) ensures atomic operations
- Workers use locks to prevent concurrent modification
- Configuration persisted in `data/config/settings.json`
- Job output captured in `data/logs/{job_id}.log`

**Thread Safety:**
- `FileLock` prevents race conditions between workers
- Lock acquisition before any read/write operation
- Automatic lock release after operation completes
- Multiple workers can safely operate concurrently

### Worker Logic

Workers operate as independent processes:
1. **Polling:** Continuously scan `data/jobs/` for pending jobs
2. **Filtering:** Check if job's `run_at` time has passed (for scheduled jobs)
3. **Locking:** Acquire lock before claiming job
4. **Execution:** Execute shell command with timeout (5 minutes)
5. **Logging:** Capture STDOUT/STDERR to log file
6. **State Update:** Update job state based on execution result
7. **Metrics:** Record execution statistics
8. **Retry Logic:** On failure, calculate backoff delay and schedule retry
9. **DLQ:** Move to DLQ if retries exhausted

## Assumptions & Trade-offs

### Design Decisions

**1. File-based Storage**
- **Decision:** Use JSON files instead of database
- **Rationale:** Simple deployment, no external dependencies, survives restarts
- **Trade-off:** Not suitable for extremely high throughput (>1000 jobs/sec)
- **Mitigation:** File locking ensures correctness at moderate scale

**2. Separate Worker Processes**
- **Decision:** Workers run as independent OS processes
- **Rationale:** True parallelism, isolation, easier monitoring, graceful shutdown
- **Trade-off:** Slightly higher overhead than threads
- **Benefit:** Better fault isolation - one worker crash doesn't affect others

**3. Exponential Backoff**
- **Decision:** Use exponential backoff for retries
- **Rationale:** Industry standard, prevents overwhelming failing services
- **Trade-off:** Failed jobs may take longer to complete
- **Benefit:** More reliable than fixed-interval retries

**4. Polling vs Push**
- **Decision:** Workers poll for jobs instead of push-based queue
- **Rationale:** Simpler implementation, no message broker required
- **Trade-off:** 1-second delay before job starts (configurable)
- **Benefit:** Easier to understand and debug

**5. Shell Command Execution**
- **Decision:** Execute arbitrary shell commands
- **Rationale:** Maximum flexibility for users
- **Trade-off:** Security risk if untrusted input (requires careful deployment)
- **Mitigation:** Document security considerations in production use

### Simplifications

1. **No Priority Queue:** All jobs processed FIFO order (could be added as enhancement)
2. **Single Machine:** Designed for single-server deployment (horizontally scaling would require distributed locking)
3. **No Web UI:** CLI-only interface for simplicity (bonus feature not implemented)
4. **Fixed Timeout:** All jobs have same 5-minute timeout (could be per-job configurable)

### Scalability Considerations

**Current capacity:**
- Handles 100-1000 jobs with multiple workers efficiently
- File-based locking works well up to ~10 concurrent workers
- Tested with 3 workers processing jobs in parallel

**To scale beyond:**
- Replace file storage with Redis or database
- Use distributed locking (Redis locks, database transactions)
- Add message queue (RabbitMQ, Kafka) for push-based architecture
- Implement worker pool management

## Testing Instructions

### Automated Test Suite

Run the comprehensive test script that verifies all features:

$ bash test_queuectl.sh

======== MANDATORY FEATURES TEST ========
[INFO] Test 1: Job enqueueing
[PASS] Job enqueueing works
[INFO] Test 2: Configuration persistence
[PASS] Config NOT hardcoded
[INFO] Test 3: File locking
[PASS] File locking implemented
[INFO] Test 4: Job persistence
[PASS] Jobs persist to disk
[INFO] Test 5: Multiple workers
[PASS] Multiple workers work (3 workers)
[INFO] Test 6: Retry mechanism and DLQ
[INFO] Waiting 20s for retry cycle...
[PASS] Retry and DLQ work

======== BONUS FEATURES TEST ========
[INFO] Test 7: Job output logging
[PASS] Output logging works (BONUS)
[INFO] Test 8: Scheduled jobs
[PASS] Scheduled jobs work (BONUS)
[INFO] Test 9: Metrics tracking
[PASS] Metrics work (BONUS)

======== TEST SUMMARY ========
Total: 9
Passed: 9
Failed: 0

✓ ALL TESTS PASSED!


### Manual Testing Scenarios

**Test 1: Basic job execution**
queuectl worker start
queuectl enqueue '{"command":"date"}'
sleep 2
queuectl list --state completed # Should show job completed
queuectl worker stop


**Test 2: Parallel execution**
queuectl worker start --count 3
queuectl enqueue '{"command":"sleep 5 && echo Job 1"}'
queuectl enqueue '{"command":"sleep 5 && echo Job 2"}'
queuectl enqueue '{"command":"sleep 5 && echo Job 3"}'

All 3 should complete in ~5 seconds (not 15 seconds sequentially)
sleep 7
queuectl list --state completed
queuectl worker stop


**Test 3: Retry mechanism**
queuectl worker start
queuectl enqueue '{"command":"exit 1"}' # Failing job

Wait for retry cycle: 2s + 4s + 8s + processing ≈ 20s
sleep 25
queuectl dlq list # Should show job in DLQ
queuectl worker stop


**Test 4: Persistence across restarts**
queuectl enqueue '{"command":"echo test"}'

Restart terminal/system
queuectl list --state pending # Job still exists


**Test 5: Scheduled jobs**
queuectl worker start
queuectl enqueue '{"command":"echo Future"}' --run-at "+10s"
sleep 5
queuectl list --state pending # Job still pending
sleep 7
queuectl list --state completed # Job now completed
queuectl worker stop


**Test 6: Configuration persistence**
queuectl config set max-retries 5
cat data/config/settings.json # Should show max_retries: 5
queuectl config show # Verify change persisted


### Verification Checklist

- [ ] Jobs can be enqueued via CLI
- [ ] Multiple workers process jobs concurrently
- [ ] Failed jobs retry with exponential backoff
- [ ] Jobs exhausting retries move to DLQ
- [ ] Jobs persist across system restarts
- [ ] Configuration changes persist to file
- [ ] Job output is logged and retrievable
- [ ] Scheduled jobs execute at correct time
- [ ] Metrics track execution statistics
- [ ] File locking prevents race conditions

## Project Structure

queuectl/
├── queuectl/
│ ├── init.py
│ ├── main.py # Entry point
│ ├── config.py # Configuration management
│ ├── metrics.py # Metrics tracking
│ ├── cli/
│ │ ├── init.py
│ │ ├── parser.py # CLI argument parsing
│ │ └── commands.py # Command handlers
│ ├── core/
│ │ ├── init.py
│ │ ├── job.py # Job model and states
│ │ ├── queue.py # Queue management logic
│ │ └── worker.py # Worker process implementation
│ └── storage/
│ ├── init.py
│ └── file_store.py # File-based persistence with locking
├── data/ # Created on first run
│ ├── jobs/ # Job state files
│ ├── dlq/ # Dead letter queue
│ ├── logs/ # Job output logs
│ ├── config/ # Configuration files
│ └── workers/ # Worker PID files
├── setup.py # Package configuration
├── requirements.txt # Python dependencies
├── test_queuectl.sh # Comprehensive test script
├── README.md # This file
└── .gitignore



## Requirements

**Python Dependencies:**
- `filelock>=3.0.0` - Thread-safe file locking

**System Requirements:**
- Python 3.7+
- Unix-like OS (Linux, macOS) or Windows with WSL
- Bash shell for test script

## Author

**Gaureesh Hegde**  
GitHub: [@GaureeshHegde](https://github.com/GaureeshHegde)

---

**Built as part of a technical assessment demonstrating:**
- System design and architecture
- CLI application development
- Background job processing
- Error handling and retry mechanisms
- File-based persistence and locking
- Concurrent process management
- Comprehensive testing and documentation