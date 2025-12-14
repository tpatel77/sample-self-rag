#!/usr/bin/env python3
"""
Main entry point for the ADK Workflow Framework.
Thin wrapper around src.cli.
"""

import sys
from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
