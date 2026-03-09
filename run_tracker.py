#!/usr/bin/env python3.12
"""
Wrapper script to run the email tracker with proper sys.path setup.
"""
import sys
import os

# Add the src directory to the path so email_tracker module can be found
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Import the main runner
from run_email_tracker import *
