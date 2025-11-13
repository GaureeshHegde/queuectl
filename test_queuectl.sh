#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASSED_TESTS++)); ((TOTAL_TESTS++)); }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; ((FAILED_TESTS++)); ((TOTAL_TESTS++)); }
log_section() { echo ""; echo -e "${YELLOW}======== $1 ========${NC}"; }

cleanup() {
    log_info "Cleaning up..."
    queuectl worker stop 2>/dev/null || true
    sleep 1
}

trap cleanup EXIT

log_section "MANDATORY FEATURES TEST"

# Test 1: Enqueue
log_info "Test 1: Job enqueueing"
if queuectl enqueue '{"command":"echo test"}' | grep -q "Job enqueued"; then
    log_success "Job enqueueing works"
else
    log_error "Job enqueueing failed"
fi

# Test 2: Config not hardcoded
log_info "Test 2: Configuration persistence"
queuectl config set max-retries 5 >/dev/null 2>&1
if grep -q '"max_retries": 5' data/config/settings.json; then
    log_success "Config NOT hardcoded"
else
    log_error "Config appears hardcoded"
fi
queuectl config set max-retries 3 >/dev/null 2>&1

# Test 3: File locking
log_info "Test 3: File locking"
if grep -r "FileLock" queuectl/storage/ >/dev/null 2>&1; then
    log_success "File locking implemented"
else
    log_error "No file locking found"
fi

# Test 4: Persistence
log_info "Test 4: Job persistence"
JOB_ID=$(queuectl enqueue '{"command":"echo persist"}' | grep "ID:" | awk '{print $2}')
if [ -f "data/jobs/${JOB_ID}.json" ]; then
    log_success "Jobs persist to disk"
else
    log_error "Jobs not persisted"
fi

# Test 5: Multiple workers
log_info "Test 5: Multiple workers"
queuectl worker start --count 3 >/dev/null 2>&1
sleep 2
WORKERS=$(ps aux | grep "queuectl.core.worker" | grep -v grep | wc -l)
if [ "$WORKERS" -eq 3 ]; then
    log_success "Multiple workers work ($WORKERS workers)"
else
    log_error "Multiple workers failed (got $WORKERS, expected 3)"
fi
queuectl worker stop >/dev/null 2>&1
sleep 2

# Test 6: Retry and DLQ
log_info "Test 6: Retry mechanism and DLQ"
queuectl worker start >/dev/null 2>&1
sleep 1
queuectl enqueue '{"command":"exit 1"}' >/dev/null 2>&1
log_info "Waiting 20s for retry cycle..."
sleep 20
DLQ_COUNT=$(queuectl dlq list 2>/dev/null | grep -c "ID:" || echo "0")
if [ "$DLQ_COUNT" -gt 0 ]; then
    log_success "Retry and DLQ work"
else
    log_error "Retry/DLQ may not work"
fi
queuectl worker stop >/dev/null 2>&1
sleep 2

log_section "BONUS FEATURES TEST"

# Test 7: Output logging
log_info "Test 7: Job output logging"
queuectl worker start >/dev/null 2>&1
sleep 1
LOG_JOB=$(queuectl enqueue '{"command":"echo bonus_test"}' | grep "ID:" | awk '{print $2}')
sleep 3
if queuectl logs "$LOG_JOB" 2>/dev/null | grep -q "bonus_test"; then
    log_success "Output logging works (BONUS)"
else
    log_error "Output logging failed (BONUS)"
fi
queuectl worker stop >/dev/null 2>&1
sleep 2

# Test 8: Scheduled jobs
log_info "Test 8: Scheduled jobs"
queuectl worker start >/dev/null 2>&1
SCHED_JOB=$(queuectl enqueue '{"command":"echo sched"}' --run-at "+5s" | grep "ID:" | awk '{print $2}')
sleep 2
if queuectl list --state completed | grep -q "$SCHED_JOB"; then
    log_error "Scheduled job ran too early (BONUS)"
else
    sleep 5
    if queuectl list --state completed | grep -q "$SCHED_JOB"; then
        log_success "Scheduled jobs work (BONUS)"
    else
        log_error "Scheduled job didn't run (BONUS)"
    fi
fi
queuectl worker stop >/dev/null 2>&1
sleep 2

# Test 9: Metrics
log_info "Test 9: Metrics tracking"
queuectl metrics --reset >/dev/null 2>&1
queuectl worker start >/dev/null 2>&1
queuectl enqueue '{"command":"echo m1"}' >/dev/null 2>&1
queuectl enqueue '{"command":"echo m2"}' >/dev/null 2>&1
sleep 5
JOBS=$(queuectl metrics | grep "Total Jobs" | awk '{print $4}')
if [ "$JOBS" -ge 2 ]; then
    log_success "Metrics work (BONUS)"
else
    log_error "Metrics failed (BONUS)"
fi
queuectl worker stop >/dev/null 2>&1

log_section "TEST SUMMARY"
echo ""
echo -e "${BLUE}Total:${NC}  $TOTAL_TESTS"
echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
echo -e "${RED}Failed:${NC} $FAILED_TESTS"
echo ""

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    exit 0
else
    PCT=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "${YELLOW}Success Rate: ${PCT}%${NC}"
    exit 1
fi
