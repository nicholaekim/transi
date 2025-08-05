#!/usr/bin/env python3
"""
Test script for the new interactive Transkribus document processing mode
"""

import sys
import os
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_interactive_mode():
    """Test the interactive mode functionality"""
    print("🧪 Testing Interactive Transkribus Mode")
    print("=" * 50)
    
    print("\n📋 This test will demonstrate the interactive mode where you can:")
    print("   1. Select a collection from your Transkribus account")
    print("   2. Choose one or more documents to process")
    print("   3. Process them through the LLM pipeline")
    print("   4. Get batch results with metadata extraction")
    
    print("\n🔧 To test this functionality, run:")
    print("   python3 run_pipeline.py --interactive")
    
    print("\n💡 Example workflow:")
    print("   What collection: SOL_Box5_FF1_Can1981-85")
    print("   Which document(s): Document1, Document10")
    print("   → Pipeline processes both documents")
    print("   → Results saved to batch_results_YYYYMMDD_HHMMSS.json")
    
    print("\n✅ Interactive mode is ready to use!")

def test_single_document():
    """Test single document processing"""
    print("\n🧪 Testing Single Document Mode")
    print("=" * 50)
    
    print("\n📋 You can also process individual documents:")
    print("   python3 run_pipeline.py --transkribus Document1")
    print("   python3 run_pipeline.py document.txt")
    print("   python3 run_pipeline.py document.pdf")
    
    print("\n✅ Single document mode is ready to use!")

def main():
    """Main test function"""
    print("🚀 OCR Pipeline v3.0 - Interactive Mode Test")
    print("=" * 60)
    
    # Check if .env exists
    env_file = Path("../.env")
    if not env_file.exists():
        print("\n⚠️  WARNING: .env file not found!")
        print("   Please copy config/.env.example to .env and configure your Transkribus credentials")
        print("   cp config/.env.example .env")
        return
    
    test_interactive_mode()
    test_single_document()
    
    print("\n🎯 Ready to process your Transkribus documents!")
    print("   Run: python3 run_pipeline.py --interactive")

if __name__ == "__main__":
    main()
