#!/usr/bin/env python3
"""
Wrapper script for running the modular impact analysis tool
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'impact_analysis'))

from impact_analysis.main import ModularImpactAnalyzer

if __name__ == "__main__":
    # Get the absolute path to the config file in the impact_analysis directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'impact_analysis', 'config_impact_analysis.yaml')
    
    # Create and run the data_analyser
    data_analyser = ModularImpactAnalyzer(config_path)
    success = data_analyser.analyze()
    
    if success:
        print("Modular impact analysis completed successfully!")
        sys.exit(0)
    else:
        print("Modular impact analysis failed. Check impact_analysis.log for details.")
        sys.exit(1)
