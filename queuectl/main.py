#!/usr/bin/env python3
"""
QueueCTL - CLI-based background job queue system
Entry point for the application
"""
from queuectl.cli.parser import parse_args
from queuectl.cli.commands import execute_command

def main():
    """Main entry point"""
    args = parse_args()
    execute_command(args)

if __name__ == '__main__':
    main()
