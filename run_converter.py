#!/usr/bin/env python3
"""
Run script for modular data conversion tool
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'converter'))

from converter.main import main

if __name__ == "__main__":
    main()
