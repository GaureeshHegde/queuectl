import argparse
import sys

def create_parser():
    """Create and configure the argument parser for queuectl CLI"""
    parser = argparse.ArgumentParser(
        prog='queuectl',
        description='CLI-based background job queue system',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Enqueue command
    enqueue_parser = subparsers.add_parser('enqueue', help='Add a new job to the queue')
    enqueue_parser.add_argument('job_data', type=str, help='Job data as JSON string (can include "run_at" for scheduled jobs)')
    enqueue_parser.add_argument('--run-at', type=str, dest='run_at', 
                                help='Schedule job for future execution (ISO format: YYYY-MM-DDTHH:MM:SS or relative like "+30s")')

    
    # Worker commands
    worker_parser = subparsers.add_parser('worker', help='Manage worker processes')
    worker_subparsers = worker_parser.add_subparsers(dest='worker_command', help='Worker operations')
    
    start_parser = worker_subparsers.add_parser('start', help='Start worker processes')
    start_parser.add_argument('--count', type=int, default=1, help='Number of workers to start')
    
    worker_subparsers.add_parser('stop', help='Stop all running workers')
    
    # Status command
    subparsers.add_parser('status', help='Show summary of all job states and active workers')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List jobs by state')
    list_parser.add_argument('--state', type=str, 
                            choices=['pending', 'processing', 'completed', 'failed', 'dead'],
                            help='Filter jobs by state')
    
    #Logs command
    logs_parser = subparsers.add_parser('logs', help='View job execution logs')
    logs_parser.add_argument('job_id', type=str, help='Job ID to view logs for')
    
    # DLQ commands
    dlq_parser = subparsers.add_parser('dlq', help='Dead Letter Queue operations')
    dlq_subparsers = dlq_parser.add_subparsers(dest='dlq_command', help='DLQ operations')
    
    dlq_subparsers.add_parser('list', help='List all jobs in DLQ')
    
    retry_parser = dlq_subparsers.add_parser('retry', help='Retry a job from DLQ')
    retry_parser.add_argument('job_id', type=str, help='Job ID to retry')
    
    # Config commands
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config operations')
    
    set_parser = config_subparsers.add_parser('set', help='Set configuration value')
    set_parser.add_argument('key', type=str, help='Configuration key (e.g., max-retries, backoff-base)')
    set_parser.add_argument('value', type=str, help='Configuration value')
    
    config_subparsers.add_parser('show', help='Show current configuration')
    
    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='View execution metrics and statistics')
    metrics_parser.add_argument('--reset', action='store_true', help='Reset all metrics')

    return parser

def parse_args(args=None):
    """Parse command line arguments"""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Show help if no command provided
    if not parsed_args.command:
        parser.print_help()
        sys.exit(1)
    
    return parsed_args
