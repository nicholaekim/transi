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
import re
from hashlib import sha256
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .advanced_model_manager import (
    AdvancedModelManager, TaskType, DocumentType, ExtractionResult, ModelConfig
)

logger = logging.getLogger(__name__)

class EnhancedLLMExtractor:
    """Advanced LLM extractor with intelligent model selection and optimization"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_manager = AdvancedModelManager()
        # HTTP session with retries
        self._session = requests.Session()
        retries = Retry(total=2, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)
        # In-memory cache only
        self._cache: Dict[str, Any] = {}
        

    
    def _make_ollama_request(self, model_name: str, prompt: str, config: ModelConfig, *, use_json: bool = False) -> Tuple[str, float]:
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
            },
            # For short, structured fields, request strict JSON and early stop
            **({"format": "json", "stop": ["\n\n", "\nExtraction:"]} if use_json else {})
        }
        
        try:
            response = self._session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=(5, 30)  # connect, read timeouts tightened for speed
            )
            response.raise_for_status()
            
            result = response.json()
            processing_time = time.time() - start_time
            
            return result.get("response", "").strip(), processing_time
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed for {model_name}: {str(e)}")
            return "", time.time() - start_time

    def detect_document_type(self, text_segments: List[str]) -> DocumentType:
        """Fast document type detection"""
        full_text = " ".join(text_segments).lower()
        
        # Simple keyword check
        if any(w in full_text for w in ['volume', 'issue', 'newsletter']):
            return DocumentType.NEWSLETTER
        elif any(w in full_text for w in ['dear', 'sincerely', 'yours']):
            return DocumentType.LETTER
        elif any(w in full_text for w in ['report', 'analysis', 'findings']):
            return DocumentType.REPORT
        else:
            return DocumentType.UNKNOWN

    def _cache_key(self, task: TaskType, text_segments: List[str]) -> str:
        joined = "\n".join(text_segments)
        h = sha256(joined.encode('utf-8')).hexdigest()
        return f"{task.value}:{h}"

    def _cache_get(self, key: str) -> Optional[ExtractionResult]:
        entry = self._cache.get(key)
        if not entry:
            return None
        return ExtractionResult(entry.get('value', ''), entry.get('confidence', 0.0), entry.get('model_used', 'cache'), entry.get('processing_time', 0.0))

    def _cache_set(self, key: str, result: ExtractionResult) -> None:
        # In-memory cache only for speed
        self._cache[key] = {
            'value': result.value,
            'confidence': result.confidence,
            'model_used': result.model_used,
            'processing_time': result.processing_time,
        }



    def _pre_extract(self, task: TaskType, text_segments: List[str]) -> Optional[ExtractionResult]:
        """Cheap regex/heuristic pre-extraction to avoid LLM calls when possible"""
        text = "\n".join(text_segments)

        # Date/year extraction
        if task == TaskType.DATE_EXTRACTION:
            # Prefer ISO-like full dates
            m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
            if m:
                value = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                conf = 0.9
                self.model_manager.record_performance("regex", task, 0.0, conf)
                return ExtractionResult(value, conf, "regex", 0.0)
            # Fallback to a standalone year
            m = re.search(r"\b(19\d{2}|20\d{2})\b", text)
            if m:
                value = m.group(1)
                conf = 0.8
                self.model_manager.record_performance("regex", task, 0.0, conf)
                return ExtractionResult(value, conf, "regex", 0.0)

        # Volume/Issue extraction
        if task == TaskType.VOLUME_ISSUE_EXTRACTION:
            # Patterns like: Volume 3, Issue 1  |  Vol. 2 No. 4
            m = re.search(r"\b(?:Volume|Vol\.)\s*(\d+)\s*[, ]\s*(?:Issue|No\.)\s*(\d+)\b", text, re.IGNORECASE)
            if m:
                value = f"Volume {m.group(1)}, Issue {m.group(2)}"
                conf = 0.85
                self.model_manager.record_performance("regex", task, 0.0, conf)
                return ExtractionResult(value, conf, "regex", 0.0)
            # Simpler issue-only patterns like: Issue #12
            m = re.search(r"\b(?:Issue|No\.)\s*#?(\d+)\b", text, re.IGNORECASE)
            if m:
                value = f"Issue {m.group(1)}"
                conf = 0.7
                self.model_manager.record_performance("regex", task, 0.0, conf)
                return ExtractionResult(value, conf, "regex", 0.0)

        # Title extraction from explicit Subject:
        if task == TaskType.TITLE_EXTRACTION:
            for line in text.splitlines():
                subj = re.match(r"^\s*Subject\s*:\s*(.+)$", line, re.IGNORECASE)
                if subj:
                    value = subj.group(1).strip()
                    if value:
                        conf = 0.75
                        self.model_manager.record_performance("regex", task, 0.0, conf)
                        return ExtractionResult(value, conf, "regex", 0.0)

        return None
    
    def _estimate_confidence(self, result: str, task: TaskType, text_segments: List[str]) -> float:
        """Fast confidence estimation"""
        if not result or result.lower() in ['no', 'none', 'not found', 'n/a']:
            return 0.1
        
        # Simple length-based confidence (fast)
        if task == TaskType.DATE_EXTRACTION:
            return 0.9 if re.match(r'\d{4}(-\d{2}-\d{2})?', result) else 0.6
        elif task == TaskType.TITLE_EXTRACTION:
            return 0.8 if 5 <= len(result) <= 120 else 0.6
        elif task == TaskType.VOLUME_ISSUE_EXTRACTION:
            return 0.9 if any(w in result.lower() for w in ['vol', 'issue', 'no']) else 0.6
        else:  # DESCRIPTION
            return 0.8 if 20 <= len(result) <= 600 else 0.6
    
    def _extract_with_model(self, task: TaskType, text_segments: List[str], 
                           model_name: str, doc_type: DocumentType) -> ExtractionResult:
        """Extract using specific model with enhanced prompting"""
        
        # Get optimized configuration
        config = self.model_manager.get_model_config(model_name, task)
        
        # Create minimal prompt (skip examples for speed)
        prompt = self.model_manager.create_enhanced_prompt(task, doc_type, text_segments, [])
        
        # Simple truncation (skip ranking for speed)
        joined = " ".join(text_segments)
        truncated = joined[:1000]  # Smaller for speed
        prompt += f"\n\nText to analyze:\n{truncated}\n\nExtraction:"
        
        # Decide if we want JSON output for compact fields
        use_json = task in (TaskType.TITLE_EXTRACTION, TaskType.DATE_EXTRACTION, TaskType.VOLUME_ISSUE_EXTRACTION)
        result_text, processing_time = self._make_ollama_request(model_name, prompt, config, use_json=use_json)

        # Parse JSON if requested
        parsed_value = None
        if use_json and result_text:
            try:
                parsed = json.loads(result_text)
                if isinstance(parsed, dict) and 'value' in parsed:
                    parsed_value = str(parsed.get('value', '')).strip()
            except Exception:
                parsed_value = None
        final_text = (parsed_value if parsed_value is not None else result_text)
        
        # Estimate confidence
        confidence = self._estimate_confidence(final_text, task, text_segments)
        
        # Skip performance recording for speed
        
        return ExtractionResult(final_text, confidence, model_name, processing_time)
    

    
    def extract_single(self, task: TaskType, text_segments: List[str], 
                       priority: str = "balanced") -> ExtractionResult:
        """Extract single field with intelligent model selection"""
        
        # Detect document type
        doc_type = self.model_manager.detect_document_type(text_segments)
        
        # Estimate text quality
        text_quality = self.model_manager.estimate_text_quality(text_segments)
        
        # Cache lookup
        ck = self._cache_key(task, text_segments)
        cached = self._cache_get(ck)
        if cached:
            logger.info(f"Cache hit for {task.value}")
            return cached

        # Cheap pre-extraction to avoid LLM calls when possible
        pre = self._pre_extract(task, text_segments)
        if pre and pre.confidence >= 0.75:
            logger.info(f"Pre-extractor satisfied {task.value} with confidence {pre.confidence:.2f}")
            self._cache_set(ck, pre)
            return pre
        
        # Select optimal model
        model_name = self.model_manager.select_optimal_model(task, doc_type, text_quality, priority)
        
        logger.info(f"Extracting {task.value} using {model_name} (doc_type: {doc_type.value}, quality: {text_quality:.2f})")
        
        # First pass extraction
        result = self._extract_with_model(task, text_segments, model_name, doc_type)
        
        # No two-pass needed with dedicated models
        
        # Save in cache
        self._cache_set(ck, result)
        
        return result
    
    def extract_parallel(self, text_segments: List[str], priority: str = "balanced") -> Dict[str, ExtractionResult]:
        """Extract all fields in parallel"""
        tasks = [TaskType.TITLE_EXTRACTION, TaskType.DATE_EXTRACTION, 
                TaskType.DESCRIPTION_EXTRACTION, TaskType.VOLUME_ISSUE_EXTRACTION]
        
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_task = {executor.submit(self.extract_single, task, text_segments): task for task in tasks}
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    results[task.value] = future.result()
                except Exception as e:
                    logger.error(f"Task {task.value} failed: {e}")
                    results[task.value] = ExtractionResult("", 0.0, "error", 0.0)
        return results
    

    

