#!/usr/bin/env python3
"""
OCR Pipeline v3.0 - Main Entry Point
Clean, organized metadata extraction pipeline with Transkribus integration
"""

import sys
import os
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline'))

from simple_pipeline import main

if __name__ == "__main__":
    main()
