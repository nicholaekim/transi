#!/usr/bin/env python3
"""
Enhanced LLM Extractor - Advanced extraction with intelligent model selection
"""

import logging
import time
import asyncio
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Any
import requests
import json
from pathlib import Path

from .advanced_model_manager import (
    AdvancedModelManager, TaskType, DocumentType, ExtractionResult, ModelConfig
)

logger = logging.getLogger(__name__)

class EnhancedLLMExtractor:
    """Advanced LLM extractor with intelligent model selection and optimization"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_manager = AdvancedModelManager()
        self.training_examples = self._load_training_examples()
        
    def _load_training_examples(self) -> Dict[TaskType, List[Dict]]:
        """Load training examples from collected data"""
        examples = {
            TaskType.DATE_EXTRACTION: [
                {"text": "6 January 1986. Dear Friends,", "result": "1986-01-06"},
                {"text": "November 15-17, 1985 meeting", "result": "1985-11-15"},
                {"text": "Published in 1984", "result": "1984"}
            ],
            TaskType.TITLE_EXTRACTION: [
                {"text": "Central American Task Force Newsletter", "result": "Central American Task Force Newsletter"},
                {"text": "Dear Members, Re: Annual General Meeting", "result": "Annual General Meeting Notice"},
                {"text": "Blessings of peace and courage for the new year!", "result": "New Year Blessings Message"}
            ],
            TaskType.DESCRIPTION_EXTRACTION: [
                {"text": "The Annual General Meeting took place...", "result": "Summary of Annual General Meeting proceedings and decisions"},
            ],
            TaskType.VOLUME_ISSUE_EXTRACTION: [
                {"text": "Volume 3, Issue 1", "result": "Volume 3, Issue 1"},
                {"text": "Vol. 2 No. 4", "result": "Volume 2, Issue 4"},
                {"text": "Newsletter #12", "result": "Issue 12"}
            ]
        }
        
        # Try to load from training data directory
        training_dir = Path("training_data")
        if training_dir.exists():
            for file_path in training_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Extract examples from training data
                        if 'corrections' in data:
                            for field, value in data['corrections'].items():
                                task = self._field_to_task(field)
                                if task and 'original_results' in data:
                                    examples[task].append({
                                        "text": data.get('source_text', '')[:200],
                                        "result": value
                                    })
                except Exception as e:
                    logger.warning(f"Could not load training data from {file_path}: {e}")
        
        return examples
    
    def _field_to_task(self, field: str) -> Optional[TaskType]:
        """Convert field name to TaskType"""
        mapping = {
            'title': TaskType.TITLE_EXTRACTION,
            'date': TaskType.DATE_EXTRACTION,
            'description': TaskType.DESCRIPTION_EXTRACTION,
            'volume_issue': TaskType.VOLUME_ISSUE_EXTRACTION
        }
        return mapping.get(field)
    
    def _make_ollama_request(self, model_name: str, prompt: str, config: ModelConfig) -> Tuple[str, float]:
        """Make optimized request to Ollama with enhanced error handling"""
        start_time = time.time()
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "num_predict": config.max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120  # Increased timeout for larger models
            )
            response.raise_for_status()
            
            result = response.json()
            processing_time = time.time() - start_time
            
            return result.get("response", "").strip(), processing_time
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed for {model_name}: {str(e)}")
            return "", time.time() - start_time
    
    def _estimate_confidence(self, result: str, task: TaskType, text_segments: List[str]) -> float:
        """Estimate confidence in extraction result"""
        if not result or result.lower() in ['no', 'none', 'not found', 'n/a']:
            return 0.1
        
        confidence = 0.5  # Base confidence
        
        # Task-specific confidence adjustments
        if task == TaskType.DATE_EXTRACTION:
            # Check for valid date patterns
            import re
            if re.match(r'\d{4}-\d{2}-\d{2}', result):
                confidence += 0.4
            elif re.match(r'\d{4}', result):
                confidence += 0.3
            
        elif task == TaskType.TITLE_EXTRACTION:
            # Check title characteristics
            if 10 <= len(result) <= 100:
                confidence += 0.3
            if result[0].isupper():
                confidence += 0.1
            
        elif task == TaskType.DESCRIPTION_EXTRACTION:
            # Check description quality
            if 50 <= len(result) <= 500:
                confidence += 0.3
            if result.count('.') >= 2:
                confidence += 0.1
            
        elif task == TaskType.VOLUME_ISSUE_EXTRACTION:
            # Check for volume/issue patterns
            if any(word in result.lower() for word in ['volume', 'vol', 'issue', 'no']):
                confidence += 0.4
        
        # Check if result appears in source text
        full_text = " ".join(text_segments).lower()
        if result.lower() in full_text:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_with_model(self, task: TaskType, text_segments: List[str], 
                           model_name: str, doc_type: DocumentType) -> ExtractionResult:
        """Extract using specific model with enhanced prompting"""
        
        # Get optimized configuration
        config = self.model_manager.get_model_config(model_name, task)
        
        # Create enhanced prompt with examples
        examples = self.training_examples.get(task, [])
        prompt = self.model_manager.create_enhanced_prompt(task, doc_type, text_segments, examples)
        
        # Add text segments to prompt
        prompt += f"\n\nText to analyze:\n{' '.join(text_segments)}\n\nExtraction:"
        
        # Make request
        result, processing_time = self._make_ollama_request(model_name, prompt, config)
        
        # Estimate confidence
        confidence = self._estimate_confidence(result, task, text_segments)
        
        # Record performance
        self.model_manager.record_performance(model_name, task, processing_time, confidence)
        
        return ExtractionResult(result, confidence, model_name, processing_time)
    
    def _two_pass_extraction(self, task: TaskType, text_segments: List[str], 
                           doc_type: DocumentType, first_result: ExtractionResult) -> ExtractionResult:
        """Perform second-pass extraction with different model"""
        
        # Select different model for second pass
        if first_result.model_used == "llama3.1:8b":
            second_model = "granite3.2-vision"
        elif first_result.model_used == "granite3.2-vision":
            second_model = "llama3.1:70b"
        else:
            second_model = "granite3.2-vision"
        
        logger.info(f"Performing second-pass extraction with {second_model}")
        
        # Extract with second model
        second_result = self._extract_with_model(task, text_segments, second_model, doc_type)
        
        # Choose best result based on confidence
        if second_result.confidence > first_result.confidence:
            logger.info(f"Second-pass improved confidence: {first_result.confidence:.2f} -> {second_result.confidence:.2f}")
            return second_result
        else:
            logger.info(f"First-pass result retained (confidence: {first_result.confidence:.2f})")
            return first_result
    
    def extract_single(self, task: TaskType, text_segments: List[str], 
                      priority: str = "balanced") -> ExtractionResult:
        """Extract single field with intelligent model selection"""
        
        # Detect document type
        doc_type = self.model_manager.detect_document_type(text_segments)
        
        # Estimate text quality
        text_quality = self.model_manager.estimate_text_quality(text_segments)
        
        # Select optimal model
        model_name = self.model_manager.select_optimal_model(task, doc_type, text_quality, priority)
        
        logger.info(f"Extracting {task.value} using {model_name} (doc_type: {doc_type.value}, quality: {text_quality:.2f})")
        
        # First pass extraction
        result = self._extract_with_model(task, text_segments, model_name, doc_type)
        
        # Check if second pass is needed
        if self.model_manager.should_use_two_pass(task, result.confidence, doc_type):
            result = self._two_pass_extraction(task, text_segments, doc_type, result)
        
        return result
    
    def extract_parallel(self, text_segments: List[str], priority: str = "balanced") -> Dict[str, ExtractionResult]:
        """Extract all fields in parallel for maximum speed"""
        
        tasks = [
            TaskType.TITLE_EXTRACTION,
            TaskType.DATE_EXTRACTION,
            TaskType.DESCRIPTION_EXTRACTION,
            TaskType.VOLUME_ISSUE_EXTRACTION
        ]
        
        results = {}
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.extract_single, task, text_segments, priority): task
                for task in tasks
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.value] = result
                    logger.info(f"Completed {task.value}: confidence={result.confidence:.2f}, time={result.processing_time:.2f}s")
                except Exception as e:
                    logger.error(f"Task {task.value} failed: {str(e)}")
                    results[task.value] = ExtractionResult("", 0.0, "error", 0.0)
        
        return results
    
    def extract_with_consensus(self, task: TaskType, text_segments: List[str]) -> ExtractionResult:
        """Extract using multiple models and consensus"""
        
        doc_type = self.model_manager.detect_document_type(text_segments)
        
        # Use 2-3 different models
        models = ["llama3.1:8b", "granite3.2-vision", "llama3.1:70b"]
        results = []
        
        for model in models[:2]:  # Use 2 models for consensus
            try:
                result = self._extract_with_model(task, text_segments, model, doc_type)
                results.append(result)
            except Exception as e:
                logger.error(f"Consensus extraction failed for {model}: {e}")
        
        if not results:
            return ExtractionResult("", 0.0, "consensus_failed", 0.0)
        
        # Simple consensus: choose highest confidence
        best_result = max(results, key=lambda r: r.confidence)
        
        # If results are very different but confidences are similar, prefer more conservative result
        if len(results) > 1:
            confidence_diff = abs(results[0].confidence - results[1].confidence)
            if confidence_diff < 0.2 and results[0].value != results[1].value:
                # Choose shorter, more conservative result for titles
                if task == TaskType.TITLE_EXTRACTION:
                    best_result = min(results, key=lambda r: len(r.value))
        
        # Mark as consensus result
        best_result.model_used = f"consensus({best_result.model_used})"
        
        return best_result
    
    # Legacy interface methods for backward compatibility
    def extract_title(self, text_segments: List[str]) -> str:
        """Extract title (legacy interface)"""
        result = self.extract_single(TaskType.TITLE_EXTRACTION, text_segments)
        return result.value
    
    def extract_date(self, text_segments: List[str]) -> str:
        """Extract date (legacy interface)"""
        result = self.extract_single(TaskType.DATE_EXTRACTION, text_segments)
        return result.value
    
    def extract_description(self, text_segments: List[str]) -> str:
        """Extract description (legacy interface)"""
        result = self.extract_single(TaskType.DESCRIPTION_EXTRACTION, text_segments)
        return result.value
    
    def extract_volume_issue(self, text_segments: List[str]) -> str:
        """Extract volume/issue (legacy interface)"""
        result = self.extract_single(TaskType.VOLUME_ISSUE_EXTRACTION, text_segments)
        return result.value
