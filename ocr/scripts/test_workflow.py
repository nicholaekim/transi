#!/usr/bin/env python3
"""
Test workflow for OCR Pipeline v3.0 with Transkribus integration
Demonstrates both PDF and text file processing capabilities
"""

import os
import sys
import time
from pathlib import Path

def test_text_file_processing():
    """Test processing with a sample text file"""
    print("🧪 Testing text file processing...")
    
    # Create sample text file
    sample_text = """
    Historical Document Analysis
    
    Date: March 15, 1923
    
    This document contains important historical information about the development
    of early 20th century industrial processes. The content spans multiple pages
    and includes detailed technical specifications and procedural guidelines.
    
    Volume 12, Issue 3
    
    The document provides comprehensive coverage of manufacturing techniques
    that were revolutionary for their time period.
    """
    
    test_file = Path("data/temp/sample_document.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(sample_text)
    
    print(f"📝 Created sample text file: {test_file}")
    
    # Test different modes
    test_commands = [
        f"python3 run_pipeline.py {test_file} --mode parallel --priority speed",
        f"python3 run_pipeline.py {test_file} --mode consensus --priority accuracy",
        f"python3 run_pipeline.py {test_file} --no-feedback"
    ]
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n🔄 Test {i}: {cmd}")
        print("   (Run this command manually to test)")
    
    return str(test_file)

def check_transkribus_setup():
    """Check if Transkribus credentials are configured"""
    print("🔍 Checking Transkribus setup...")
    
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "your_email@example.com" in content:
                print("⚠️  Transkribus credentials not configured")
                print("   Edit .env file with your Transkribus credentials")
                return False
            else:
                print("✅ Transkribus credentials configured")
                return True
    else:
        print("⚠️  .env file not found")
        print("   Copy .env.example to .env and configure credentials")
        return False

def check_ollama_status():
    """Check if Ollama is running and models are available"""
    print("🤖 Checking Ollama status...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            required_models = ['llama3.1:8b', 'llama3.1:70b']
            missing_models = [m for m in required_models if not any(m in name for name in model_names)]
            
            if missing_models:
                print(f"⚠️  Missing models: {missing_models}")
                print("   Run: ollama pull <model_name> for each missing model")
                return False
            else:
                print("✅ All required models available")
                return True
        else:
            print("❌ Ollama not responding")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("   Start Ollama with: ollama serve")
        return False

def main():
    """Run complete test workflow"""
    print("🚀 OCR Pipeline v3.0 - Test Workflow")
    print("=" * 50)
    
    # Check system requirements
    ollama_ok = check_ollama_status()
    transkribus_ok = check_transkribus_setup()
    
    print("\n📋 System Status:")
    print(f"   Ollama: {'✅' if ollama_ok else '❌'}")
    print(f"   Transkribus: {'✅' if transkribus_ok else '⚠️'}")
    
    # Create test text file
    print("\n" + "=" * 50)
    test_file = test_text_file_processing()
    
    print("\n" + "=" * 50)
    print("🎯 Ready to test!")
    print(f"\n📝 Text File Processing:")
    print(f"   python3 run_pipeline.py {test_file}")
    
    if transkribus_ok:
        print("\n📄 PDF Processing (requires PDF file):")
        print("   python3 run_pipeline.py your_document.pdf")
    else:
        print("\n📄 PDF Processing:")
        print("   Configure Transkribus credentials first")
    
    print("\n📚 For more options:")
    print("   python3 run_pipeline.py --help")

if __name__ == "__main__":
    main()
