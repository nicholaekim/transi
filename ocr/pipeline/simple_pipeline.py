#!/usr/bin/env python3
"""
Advanced OCR Pipeline - Intelligent processing with enhanced model management
Transkribus Text File → Smart Analysis → Parallel LLM Processing → Results → Automatic Feedback
"""

import sys
import os
import json
import subprocess
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add pipeline core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.enhanced_extractor import EnhancedLLMExtractor, TaskType
from core.smart_document_analyzer import SmartDocumentAnalyzer
from core.transkribus_client import TranskribusClient
from core.advanced_model_manager import AdvancedModelManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedPipeline:
    """Advanced pipeline with intelligent model selection and parallel processing"""
    
    def __init__(self):
        """Initialize the advanced pipeline"""
        self.setup_directories()
        self.model_manager = AdvancedModelManager()
        self.document_analyzer = SmartDocumentAnalyzer()
        self.extractor = EnhancedLLMExtractor(self.model_manager)
        self.transkribus_client = None
        
        logger.info("🚀 Advanced OCR Pipeline v3.0 initialized")
    
    def setup_directories(self):
        """Create necessary directories"""
        # Use relative paths from project root
        project_root = Path(__file__).parent.parent
        self.end_pipeline_dir = project_root / "data" / "output"
        self.temp_dir = project_root / "data" / "temp"
        
        self.end_pipeline_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def init_transkribus_client(self) -> bool:
        """Initialize Transkribus client with credentials"""
        try:
            if not self.transkribus_client:
                self.transkribus_client = TranskribusClient()
                return self.transkribus_client.login()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Transkribus client: {e}")
            return False
    
    def process_pdf_with_transkribus(self, pdf_path: Path) -> Optional[Path]:
        """Process PDF using Transkribus API"""
        if not self.transkribus_client:
            logger.error("Transkribus client not initialized")
            return None
        
        try:
            logger.info(f"📤 Uploading PDF to Transkribus: {pdf_path.name}")
            
            # Upload and process PDF
            extracted_text = self.transkribus_client.process_pdf(str(pdf_path))
            
            if extracted_text:
                # Save extracted text for manual correction
                text_file = self.temp_dir / f"{pdf_path.stem}_extracted.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                
                logger.info(f"📝 Text extracted and saved to: {text_file}")
                logger.info("\n" + "="*50)
                logger.info("📋 MANUAL CORRECTION STEP")
                logger.info(f"Please review and correct the extracted text in: {text_file}")
                logger.info("Press Enter when ready to continue with corrected text...")
                logger.info("="*50)
                
                input()  # Wait for user confirmation
                
                return text_file
            else:
                logger.error("Failed to extract text from PDF")
                return None
                
        except Exception as e:
            logger.error(f"Error processing PDF with Transkribus: {e}")
            return None
    
    def download_transkribus_document(self, document_name: str) -> Optional[Path]:
        """Download existing document from Transkribus by name"""
        if not self.transkribus_client:
            logger.error("Transkribus client not initialized")
            return None
        
        try:
            logger.info(f"🔍 Searching for document: {document_name}")
            
            # Download document text
            text_file = self.temp_dir / f"{document_name}_downloaded.txt"
            result = self.transkribus_client.download_document_by_name(
                document_name, 
                str(text_file)
            )
            
            if result:
                logger.info(f"📥 Document downloaded: {text_file}")
                return text_file
            else:
                logger.error(f"Failed to download document: {document_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return None
    
    def interactive_transkribus_mode(self) -> List[Dict]:
        """Interactive mode for selecting and processing multiple Transkribus documents"""
        if not self.transkribus_client:
            logger.error("Transkribus client not initialized")
            return []
        
        try:
            print("\n🎆 Interactive Transkribus Document Processing")
            print("=" * 60)
            
            # Select collection
            collection = self.transkribus_client.interactive_collection_selection()
            if not collection:
                return []
            
            collection_id = collection['colId']
            collection_name = collection.get('colName', 'Unknown')
            
            # Select documents
            selected_docs = self.transkribus_client.interactive_document_selection(
                collection_id, collection_name
            )
            
            if not selected_docs:
                return []
            
            print(f"\n🚀 Processing {len(selected_docs)} document(s) from '{collection_name}'...")
            print("=" * 60)
            
            results = []
            
            for i, doc in enumerate(selected_docs, 1):
                doc_title = doc.get('title', 'Untitled')
                doc_id = doc.get('docId')
                
                print(f"\n📄 Processing {i}/{len(selected_docs)}: {doc_title}")
                print("-" * 40)
                
                try:
                    # Get document text
                    text = self.transkribus_client.get_document_text(collection_id, doc_id)
                    
                    if text:
                        # Process through LLM pipeline
                        result = self.process_text_content(
                            text, 
                            document_name=doc_title,
                            mode='parallel',  # Default mode for batch processing
                            priority='balanced'
                        )
                        
                        if result:
                            result['source_document'] = doc_title
                            result['source_collection'] = collection_name
                            results.append(result)
                            print(f"✅ Successfully processed: {doc_title}")
                        else:
                            print(f"❌ Failed to process: {doc_title}")
                    else:
                        print(f"❌ Failed to get text for: {doc_title}")
                        
                except Exception as e:
                    print(f"❌ Error processing {doc_title}: {e}")
                    logger.error(f"Error processing document {doc_title}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            return []
    
    def analyze_document(self, text: str) -> Dict:
        """Perform comprehensive document analysis"""
        logger.info("🔍 Analyzing document structure and quality...")
        
        # Get document structure analysis
        structure = self.analyzer.analyze_document_structure(text)
        
        # Get quality metrics
        quality = self.analyzer.get_document_quality_metrics(text)
        
        # Detect document type
        segments = self.analyzer.segment_text_intelligently(text)
        doc_type = self.model_manager.detect_document_type([seg.content for seg in segments])
        
        analysis = {
            'structure': structure,
            'quality': quality,
            'document_type': doc_type.value,
            'total_segments': len(segments),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📋 Document analysis complete: type={doc_type.value}, quality={quality['overall_quality']:.2f}")
        return analysis
    
    def extract_metadata_parallel(self, text: str, priority: str = "balanced") -> Dict:
        """Extract all metadata fields in parallel with intelligent optimization"""
        logger.info(f"⚡ Starting parallel extraction (priority: {priority})...")
        start_time = time.time()
        
        # Create optimized segments for each task
        task_segments = {
            'title': self.analyzer.create_optimized_segments_for_task(text, 'title'),
            'date': self.analyzer.create_optimized_segments_for_task(text, 'date'),
            'description': self.analyzer.create_optimized_segments_for_task(text, 'description'),
            'volume_issue': self.analyzer.create_optimized_segments_for_task(text, 'volume_issue')
        }
        
        # Use general segments as fallback
        general_segments = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract using parallel processing
        results = self.extractor.extract_parallel(general_segments, priority)
        
        # Convert to legacy format with enhanced metadata
        metadata = {
            'title': results.get('title', type('obj', (object,), {'value': '', 'confidence': 0.0, 'model_used': 'none', 'processing_time': 0.0})).value,
            'date': results.get('date', type('obj', (object,), {'value': '', 'confidence': 0.0, 'model_used': 'none', 'processing_time': 0.0})).value,
            'description': results.get('description', type('obj', (object,), {'value': '', 'confidence': 0.0, 'model_used': 'none', 'processing_time': 0.0})).value,
            'volume_issue': results.get('volume_issue', type('obj', (object,), {'value': '', 'confidence': 0.0, 'model_used': 'none', 'processing_time': 0.0})).value,
            
            # Enhanced metadata
            'extraction_metadata': {
                'total_processing_time': time.time() - start_time,
                'extraction_timestamp': datetime.now().isoformat(),
                'priority_mode': priority,
                'field_details': {
                    field: {
                        'confidence': results.get(field, type('obj', (object,), {'confidence': 0.0})).confidence,
                        'model_used': results.get(field, type('obj', (object,), {'model_used': 'none'})).model_used,
                        'processing_time': results.get(field, type('obj', (object,), {'processing_time': 0.0})).processing_time
                    } for field in ['title', 'date', 'description', 'volume_issue']
                }
            }
        }
        
        # Log results
        total_time = time.time() - start_time
        avg_confidence = sum(results[field].confidence for field in results) / len(results)
        
        logger.info(f"✅ Parallel extraction complete: {total_time:.2f}s, avg_confidence={avg_confidence:.2f}")
        
        return metadata
    
    def extract_metadata_consensus(self, text: str) -> Dict:
        """Extract metadata using consensus from multiple models"""
        logger.info("🤝 Starting consensus-based extraction...")
        start_time = time.time()
        
        general_segments = [line.strip() for line in text.split('\n') if line.strip()]
        
        tasks = [TaskType.TITLE_EXTRACTION, TaskType.DATE_EXTRACTION, 
                TaskType.DESCRIPTION_EXTRACTION, TaskType.VOLUME_ISSUE_EXTRACTION]
        
        results = {}
        for task in tasks:
            result = self.extractor.extract_with_consensus(task, general_segments)
            field_name = task.value
            results[field_name] = result
            logger.info(f"🎯 Consensus {field_name}: confidence={result.confidence:.2f}")
        
        # Convert to metadata format
        metadata = {
            'title': results['title'].value,
            'date': results['date'].value,
            'description': results['description'].value,
            'volume_issue': results['volume_issue'].value,
            
            'extraction_metadata': {
                'total_processing_time': time.time() - start_time,
                'extraction_timestamp': datetime.now().isoformat(),
                'extraction_method': 'consensus',
                'field_details': {
                    field: {
                        'confidence': results[field].confidence,
                        'model_used': results[field].model_used,
                        'processing_time': results[field].processing_time
                    } for field in results
                }
            }
        }
        
        logger.info(f"✅ Consensus extraction complete: {time.time() - start_time:.2f}s")
        return metadata
    
    def run_feedback_analysis(self, results_file: str, source_text_file: str):
        """Run automatic feedback analysis after pipeline completion"""
        try:
            logger.info("📊 Starting accuracy analysis...")
            cmd = [sys.executable, "fine_tune_and_train.py", results_file, "--source-text", source_text_file]
            
            print("📊 Analyzing extraction accuracy...")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                # Print the analysis output
                print(result.stdout)
                
                # Check if accuracy is low and offer interactive correction
                if "Low accuracy score" in result.stdout or "OVERALL ACCURACY SCORE: " in result.stdout:
                    # Extract score from output
                    for line in result.stdout.split('\n'):
                        if "OVERALL ACCURACY SCORE:" in line:
                            try:
                                score_str = line.split(":")[1].strip().split("/")[0]
                                score = float(score_str)
                                if score < 7.5:
                                    print(f"\n⚠️ Accuracy score ({score:.1f}/10) could be improved.")
                                    print("🔧 Would you like to run interactive correction to improve future results? (y/n): ", end="")
                                    response = input().strip().lower()
                                    if response.startswith('y'):
                                        self.run_interactive_correction(results_file)
                                break
                            except (ValueError, IndexError):
                                pass
            else:
                print(f"⚠️ Feedback analysis failed: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Could not run feedback analysis: {str(e)}")
            print("💡 You can manually run: python3 fine_tune_and_train.py [results_file] --interactive")
    
    def run_interactive_correction(self, results_file: str):
        """Run interactive correction session"""
        try:
            cmd = [sys.executable, "fine_tune_and_train.py", results_file, "--interactive"]
            subprocess.run(cmd, cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"⚠️ Interactive correction failed: {str(e)}")
    
    def process_document(self, text_file_path: str, mode: str = "parallel", priority: str = "balanced") -> Dict:
        """Process document with specified mode and priority"""
        logger.info(f"🎯 Processing document: {text_file_path} (mode: {mode}, priority: {priority})")
        
        # Read text file
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"❌ Failed to read file {text_file_path}: {e}")
            return {}
        
        if not text.strip():
            logger.error("❌ File is empty or contains no readable text")
            return {}
        
        # Analyze document
        analysis = self.analyze_document(text)
        
        # Choose extraction method based on mode
        if mode == "consensus":
            metadata = self.extract_metadata_consensus(text)
        elif mode == "parallel":
            metadata = self.extract_metadata_parallel(text, priority)
        else:
            logger.warning(f"Unknown mode '{mode}', defaulting to parallel")
            metadata = self.extract_metadata_parallel(text, priority)
        
        # Add document analysis to metadata
        metadata['document_analysis'] = analysis
        
        return metadata
    
    def save_results(self, metadata: Dict, source_file: str) -> str:
        """Save extraction results to JSON file"""
        # Create filename based on source
        source_name = Path(source_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.end_pipeline_dir / f"{source_name}_results_{timestamp}.json"
        
        # Add source file info
        metadata['source_file'] = str(source_file)
        metadata['results_file'] = str(results_file)
        metadata['pipeline_version'] = "3.0_advanced"
        
        # Save to file
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Results saved to: {results_file}")
            return str(results_file)
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
            return ""
    
    def run_full_pipeline(self, text_file_path: str, mode: str = "parallel", priority: str = "balanced") -> str:
        """Run the complete pipeline with automatic feedback"""
        start_time = time.time()
        
        print(f"\n🚀 Advanced OCR Pipeline v3.0")
        print(f"📄 Processing: {Path(text_file_path).name}")
        print(f"⚙️ Mode: {mode}, Priority: {priority}")
        print("=" * 50)
        
        # Process document
        metadata = self.process_document(text_file_path, mode, priority)
        
        if not metadata:
            print("❌ Pipeline failed - no results generated")
            return ""
        
        # Save results
        results_file = self.save_results(metadata, text_file_path)
        
        if not results_file:
            print("❌ Pipeline failed - could not save results")
            return ""
        
        # Display results summary
        self.display_results_summary(metadata)
        
        # Run automatic feedback analysis
        self.run_feedback_analysis(results_file, text_file_path)
        
        total_time = time.time() - start_time
        print(f"\n✅ Pipeline completed in {total_time:.2f} seconds")
        print(f"📁 Results saved to: {results_file}")
        
        return results_file
    
    def display_results_summary(self, metadata: Dict):
        """Display a summary of extraction results"""
        print("\n📋 EXTRACTION RESULTS")
        print("=" * 30)
        
        # Basic results
        print(f"📝 Title: {metadata.get('title', 'Not found')}")
        print(f"📅 Date: {metadata.get('date', 'Not found')}")
        print(f"📄 Description: {metadata.get('description', 'Not found')[:100]}{'...' if len(metadata.get('description', '')) > 100 else ''}")
        print(f"📊 Volume/Issue: {metadata.get('volume_issue', 'Not found')}")
        
        # Enhanced metadata if available
        if 'extraction_metadata' in metadata:
            ext_meta = metadata['extraction_metadata']
            print(f"\n⚡ Processing Time: {ext_meta.get('total_processing_time', 0):.2f}s")
            print(f"🎯 Extraction Method: {ext_meta.get('extraction_method', ext_meta.get('priority_mode', 'unknown'))}")
            
            if 'field_details' in ext_meta:
                print("\n🔍 CONFIDENCE SCORES")
                for field, details in ext_meta['field_details'].items():
                    confidence = details.get('confidence', 0)
                    model = details.get('model_used', 'unknown')
                    time_taken = details.get('processing_time', 0)
                    
                    confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                    print(f"  {confidence_emoji} {field.title()}: {confidence:.2f} ({model}, {time_taken:.2f}s)")
        
        # Document analysis if available
        if 'document_analysis' in metadata:
            doc_analysis = metadata['document_analysis']
            doc_type = doc_analysis.get('document_type', 'unknown')
            quality = doc_analysis.get('quality', {}).get('overall_quality', 0)
            
            print(f"\n📄 Document Type: {doc_type.title()}")
            print(f"✨ Text Quality: {quality:.2f}")


def main():
    """Main pipeline function"""
    parser = argparse.ArgumentParser(
        description="Advanced OCR Pipeline v3.0 - Intelligent metadata extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 simple_pipeline.py document.txt
  python3 simple_pipeline.py document.pdf
  python3 simple_pipeline.py --transkribus Document1
  python3 simple_pipeline.py --interactive
  python3 simple_pipeline.py document.txt --mode consensus

Modes:
  parallel  - Extract all fields simultaneously (fastest)
  consensus - Use multiple models for higher accuracy (slower)

Priorities:
  speed     - Optimize for fastest processing
  balanced  - Balance speed and accuracy (default)
  accuracy  - Optimize for highest accuracy

Transkribus:
  --transkribus DOCUMENT_NAME  - Download existing document from Transkribus
  --interactive                - Interactive mode to select collection and documents"""
    )
    
    parser.add_argument('input_file', nargs='?', help='Path to PDF/text file OR document name (with --transkribus)')
    parser.add_argument('--transkribus', metavar='DOCUMENT_NAME', 
                       help='Download existing document from Transkribus by name')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive mode to select collection and documents from Transkribus')
    parser.add_argument('--mode', choices=['parallel', 'consensus'], default='parallel',
                       help='Extraction mode (default: parallel)')
    parser.add_argument('--priority', choices=['speed', 'balanced', 'accuracy'], default='balanced',
                       help='Processing priority (default: balanced)')
    parser.add_argument('--no-feedback', action='store_true',
                       help='Skip automatic feedback analysis')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.input_file and not args.transkribus and not args.interactive:
        parser.error('Must provide either input_file, --transkribus DOCUMENT_NAME, or --interactive')
    
    if sum(bool(x) for x in [args.input_file, args.transkribus, args.interactive]) > 1:
        parser.error('Cannot use multiple input methods at the same time')
    
    pipeline = AdvancedPipeline()
    
    try:
        # Handle interactive mode
        if args.interactive:
            if not pipeline.init_transkribus_client():
                logger.error("Failed to initialize Transkribus client. Check your credentials.")
                return
            
            # Run interactive mode
            results = pipeline.interactive_transkribus_mode()
            
            if results:
                # Save batch results
                batch_results = {
                    'batch_processing': True,
                    'total_documents': len(results),
                    'processed_at': datetime.now().isoformat(),
                    'documents': results
                }
                
                # Save to output directory
                output_file = pipeline.output_dir / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(batch_results, f, indent=2, ensure_ascii=False)
                
                print(f"\n🎉 Batch processing complete!")
                print(f"📊 Processed {len(results)} documents")
                print(f"💾 Results saved to: {output_file}")
                
                # Run feedback analysis if not disabled
                if not args.no_feedback:
                    print("\n🔍 Running feedback analysis...")
                    from pipeline.utils.fine_tune_and_train import run_feedback_analysis
                    run_feedback_analysis(str(output_file))
            else:
                print("\n❌ No documents were processed")
            
            return
        
        # Handle single Transkribus document download
        elif args.transkribus:
            if not pipeline.init_transkribus_client():
                logger.error("Failed to initialize Transkribus client. Check your credentials.")
                return
            
            text_file_path = pipeline.download_transkribus_document(args.transkribus)
            if not text_file_path:
                logger.error(f"Failed to download document: {args.transkribus}")
                return
            
            # Read downloaded text
            with open(text_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
        
        # Handle file input
        else:
            input_path = Path(args.input_file)
            
            # Check if input is PDF or text file
            if input_path.suffix.lower() == '.pdf':
                if not input_path.exists():
                    logger.error(f"PDF file not found: {input_path}")
                    return
                
                # Initialize Transkribus for PDF processing
                if not pipeline.init_transkribus_client():
                    logger.error("Transkribus client required for PDF processing. Check your credentials.")
                    return
                
                # Process PDF with Transkribus
                text_file_path = pipeline.process_pdf_with_transkribus(input_path)
                if not text_file_path:
                    logger.error("Failed to process PDF")
                    return
                
                # Read processed text
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
                    
            elif input_path.suffix.lower() == '.txt':
                if not input_path.exists():
                    logger.error(f"Text file not found: {input_path}")
                    return
                
                # Read text file
                with open(input_path, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
            
            else:
                logger.error(f"Unsupported file type: {input_path.suffix}. Use .pdf or .txt files.")
                return
        
        # Validate text content
        if not text_content:
            logger.error("No text content to process")
            return
        
        # Process the text content
        document_name = args.transkribus or Path(args.input_file).stem
        result = pipeline.process_text_content(
            text_content,
            document_name=document_name,
            mode=args.mode,
            priority=args.priority
        )
        
        if result:
            # Save results
            output_file = pipeline.output_dir / f"{document_name}_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Processing complete!")
            print(f"💾 Results saved to: {output_file}")
            
            # Run feedback analysis if not disabled
            if not args.no_feedback:
                print("\n🔍 Running feedback analysis...")
                from pipeline.utils.fine_tune_and_train import run_feedback_analysis
                run_feedback_analysis(str(output_file))
        else:
            logger.error("Failed to process document")
            
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
