#!/usr/bin/env python3
"""
Wrapper script for running the modular impact analysis tool
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'impact_analysis'))

from impact_analysis.main import main

if __name__ == "__main__":
    main()
