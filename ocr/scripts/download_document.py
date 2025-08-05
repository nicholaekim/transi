#!/usr/bin/env python3
"""
Simple script to download a document from Transkribus by name
"""

import sys
import os
from pathlib import Path

# Add pipeline core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pipeline', 'core'))

from transkribus_client import TranskribusClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 download_document.py DOCUMENT_NAME")
        print("Example: python3 download_document.py Document1")
        sys.exit(1)
    
    document_name = sys.argv[1]
    
    try:
        # Initialize Transkribus client
        print(f"🔍 Searching for document: {document_name}")
        client = TranskribusClient()
        
        # Login
        if not client.login():
            print("❌ Failed to login to Transkribus")
            sys.exit(1)
        
        # Download document
        output_path = f"data/temp/{document_name}_downloaded.txt"
        result = client.download_document_by_name(document_name, output_path)
        
        if result:
            print(f"✅ Document downloaded successfully: {output_path}")
            print(f"📄 Now you can process it with:")
            print(f"   python3 run_pipeline.py {output_path}")
        else:
            print(f"❌ Failed to download document: {document_name}")
            
            # List available documents
            print("\n📚 Available documents:")
            collections = client.get_collections()
            if collections:
                for collection in collections:
                    collection_id = collection.get('colId')
                    collection_name = collection.get('colName', 'Unknown')
                    print(f"\n📁 Collection: {collection_name}")
                    
                    documents = client.get_documents_in_collection(collection_id)
                    if documents:
                        for doc in documents:
                            doc_title = doc.get('title', 'Untitled')
                            print(f"   📄 {doc_title}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
