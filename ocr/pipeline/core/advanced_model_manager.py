#!/usr/bin/env python3
"""
Advanced Model Manager - Intelligent model selection and optimization
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    LETTER = "letter"
    NEWSLETTER = "newsletter"
    REPORT = "report"
    ARTICLE = "article"
    UNKNOWN = "unknown"

class TaskType(Enum):
    DATE_EXTRACTION = "date"
    TITLE_EXTRACTION = "title"
    DESCRIPTION_EXTRACTION = "description"
    VOLUME_ISSUE_EXTRACTION = "volume_issue"

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int
    speed_score: int  # 1-10, higher = faster
    accuracy_score: int  # 1-10, higher = more accurate
    
class ExtractionResult:
    """Enhanced result with confidence and metadata"""
    def __init__(self, value: str, confidence: float, model_used: str, processing_time: float):
        self.value = value
        self.confidence = confidence
        self.model_used = model_used
        self.processing_time = processing_time
        self.timestamp = time.time()

class AdvancedModelManager:
    """Fast model management"""
    
    def __init__(self):
        self.models = self._initialize_models()
        self.document_type_cache = {}
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize task-specific dedicated models"""
        return {
            # Title extraction specialist
            "phi3.5:3.8b": ModelConfig(
                name="phi3.5:3.8b",
                temperature=0.1,
                top_p=0.9,
                top_k=40,
                max_tokens=64,
                speed_score=9,
                accuracy_score=9
            ),
            
            # Date extraction specialist (ultra-fast)
            "llama3.2:1b": ModelConfig(
                name="llama3.2:1b",
                temperature=0.05,
                top_p=0.8,
                top_k=20,
                max_tokens=32,
                speed_score=10,
                accuracy_score=8
            ),
            
            # Description summarization specialist
            "qwen2.5:3b": ModelConfig(
                name="qwen2.5:3b",
                temperature=0.2,
                top_p=0.9,
                top_k=40,
                max_tokens=256,
                speed_score=9,
                accuracy_score=9
            ),
            
            # Volume/Issue extraction specialist
            "gemma2:2b": ModelConfig(
                name="gemma2:2b",
                temperature=0.05,
                top_p=0.8,
                top_k=20,
                max_tokens=64,
                speed_score=10,
                accuracy_score=8
            )
        }
    
    def detect_document_type(self, text_segments: List[str]) -> DocumentType:
        """Detect document type using pattern analysis"""
        full_text = " ".join(text_segments).lower()
        
        # Cache check
        text_hash = hash(full_text[:500])  # Use first 500 chars for hashing
        if text_hash in self.document_type_cache:
            return self.document_type_cache[text_hash]
        
        # Letter indicators
        letter_patterns = [
            r'\bdear\b', r'\bsincerely\b', r'\byours\b', r'\bbest regards\b',
            r'\bfrom:\b', r'\bto:\b', r'\bsubject:\b'
        ]
        
        # Newsletter indicators
        newsletter_patterns = [
            r'\bvolume\b', r'\bissue\b', r'\bnewsletter\b', r'\bpublication\b',
            r'\beditor\b', r'\barticles?\b', r'\bfeatures?\b'
        ]
        
        # Report indicators
        report_patterns = [
            r'\breport\b', r'\banalysis\b', r'\bfindings\b', r'\bconclusion\b',
            r'\bexecutive summary\b', r'\brecommendations?\b'
        ]
        
        # Count pattern matches
        letter_score = sum(1 for pattern in letter_patterns if re.search(pattern, full_text))
        newsletter_score = sum(1 for pattern in newsletter_patterns if re.search(pattern, full_text))
        report_score = sum(1 for pattern in report_patterns if re.search(pattern, full_text))
        
        # Determine document type
        if letter_score >= 2:
            doc_type = DocumentType.LETTER
        elif newsletter_score >= 2:
            doc_type = DocumentType.NEWSLETTER
        elif report_score >= 2:
            doc_type = DocumentType.REPORT
        else:
            doc_type = DocumentType.UNKNOWN
        
        # Cache result
        self.document_type_cache[text_hash] = doc_type
        logger.info(f"Detected document type: {doc_type.value}")
        
        return doc_type
    
    def select_optimal_model(self, task: TaskType, doc_type: DocumentType, 
                           text_quality: float = 1.0, priority: str = "balanced") -> str:
        """Select optimal model based on task, document type, and requirements"""
        
        # Dedicated model per task (no fallbacks needed)
        task_models = {
            TaskType.TITLE_EXTRACTION: "phi3.5:3.8b",
            TaskType.DATE_EXTRACTION: "llama3.2:1b", 
            TaskType.DESCRIPTION_EXTRACTION: "qwen2.5:3b",
            TaskType.VOLUME_ISSUE_EXTRACTION: "gemma2:2b"
        }
        
        return task_models.get(task, "llama3.2:1b")
    
    def get_model_config(self, model_name: str, task: TaskType) -> ModelConfig:
        """Get pre-configured model (already optimized per task)"""
        return self.models[model_name]
    
    def create_enhanced_prompt(self, task: TaskType, doc_type: DocumentType, 
                             text_segments: List[str], examples: List[Dict] = None) -> str:
        """Create minimal prompts for speed"""
        
        prompts = {
            TaskType.DATE_EXTRACTION: "Extract the date. Return YYYY-MM-DD or YYYY only.",
            TaskType.TITLE_EXTRACTION: "Extract the main title or subject.",
            TaskType.DESCRIPTION_EXTRACTION: "Write a brief summary.",
            TaskType.VOLUME_ISSUE_EXTRACTION: "Extract volume and issue numbers."
        }
        
        return prompts.get(task, "Extract the requested information.")
    
    def estimate_text_quality(self, text_segments: List[str]) -> float:
        """Fast text quality check"""
        full_text = " ".join(text_segments)
        if len(full_text) < 10:
            return 0.5
        # Simple heuristic: if text has reasonable length and basic punctuation
        return 0.8 if any(c in full_text for c in '.,!?') else 0.6
    
    def should_use_two_pass(self, task: TaskType, confidence: float, doc_type: DocumentType) -> bool:
        """No two-pass needed with dedicated models"""
        return False
    

