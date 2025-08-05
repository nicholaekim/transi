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
    """Intelligent model management with dynamic selection and optimization"""
    
    def __init__(self):
        self.models = self._initialize_models()
        self.document_type_cache = {}
        self.performance_history = {}
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize available models with their configurations"""
        return {
            # Fast, lightweight models for simple tasks
            "llama3.1:8b": ModelConfig(
                name="llama3.1:8b",
                temperature=0.1,
                top_p=0.9,
                top_k=40,
                max_tokens=200,
                speed_score=9,
                accuracy_score=7
            ),
            
            # Balanced model for most tasks
            "granite3.2-vision": ModelConfig(
                name="granite3.2-vision",
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                max_tokens=500,
                speed_score=7,
                accuracy_score=8
            ),
            
            # High-accuracy model for complex tasks
            "llama3.1:70b": ModelConfig(
                name="llama3.1:70b",
                temperature=0.5,
                top_p=0.9,
                top_k=50,
                max_tokens=1000,
                speed_score=4,
                accuracy_score=10
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
        
        # Task-specific model preferences
        task_preferences = {
            TaskType.DATE_EXTRACTION: ["llama3.1:8b", "granite3.2-vision"],
            TaskType.TITLE_EXTRACTION: ["granite3.2-vision", "llama3.1:8b"],
            TaskType.DESCRIPTION_EXTRACTION: ["llama3.1:70b", "granite3.2-vision"],
            TaskType.VOLUME_ISSUE_EXTRACTION: ["llama3.1:8b", "granite3.2-vision"]
        }
        
        # Document type adjustments
        if doc_type == DocumentType.NEWSLETTER:
            # Newsletters often have complex layouts, prefer vision model
            if task in [TaskType.TITLE_EXTRACTION, TaskType.VOLUME_ISSUE_EXTRACTION]:
                return "granite3.2-vision"
        
        elif doc_type == DocumentType.LETTER:
            # Letters are usually simpler, can use faster models
            if task == TaskType.DATE_EXTRACTION:
                return "llama3.1:8b"
        
        # Text quality adjustments
        if text_quality < 0.7:  # Poor OCR quality
            # Use more robust models for poor quality text
            return "granite3.2-vision"
        
        # Priority-based selection
        preferred_models = task_preferences.get(task, ["granite3.2-vision"])
        
        if priority == "speed":
            # Sort by speed score
            return max(preferred_models, key=lambda m: self.models[m].speed_score)
        elif priority == "accuracy":
            # Sort by accuracy score
            return max(preferred_models, key=lambda m: self.models[m].accuracy_score)
        else:  # balanced
            # Balance speed and accuracy
            return max(preferred_models, 
                      key=lambda m: (self.models[m].speed_score + self.models[m].accuracy_score) / 2)
    
    def get_model_config(self, model_name: str, task: TaskType) -> ModelConfig:
        """Get optimized configuration for specific model and task"""
        base_config = self.models[model_name]
        
        # Task-specific temperature adjustments
        if task in [TaskType.DATE_EXTRACTION, TaskType.VOLUME_ISSUE_EXTRACTION]:
            # Lower temperature for factual extractions
            base_config.temperature = min(0.2, base_config.temperature)
        elif task == TaskType.DESCRIPTION_EXTRACTION:
            # Higher temperature for creative summarization
            base_config.temperature = max(0.5, base_config.temperature)
        
        return base_config
    
    def create_enhanced_prompt(self, task: TaskType, doc_type: DocumentType, 
                             text_segments: List[str], examples: List[Dict] = None) -> str:
        """Create optimized prompts with examples and context"""
        
        # Base prompts with document type awareness
        base_prompts = {
            TaskType.DATE_EXTRACTION: {
                DocumentType.LETTER: """Extract the date from this letter. Look for dates in headers, signatures, or explicit date mentions.
Focus on: letterhead dates, signature dates, "Dear [Name]" context dates.
Return in YYYY-MM-DD format if full date available, or YYYY if only year.""",
                
                DocumentType.NEWSLETTER: """Extract the publication date from this newsletter.
Look for: issue dates, publication information, volume/issue headers.
Return in YYYY-MM-DD format if available, or YYYY if only year.""",
                
                DocumentType.REPORT: """Extract the report date or publication date.
Look for: cover page dates, "as of" dates, publication information.
Return in YYYY-MM-DD format if available, or YYYY if only year."""
            },
            
            TaskType.TITLE_EXTRACTION: {
                DocumentType.LETTER: """Extract the main subject or title of this letter.
Look for: subject lines, main topic in opening paragraph, letter purpose.
Return a clear, concise title that captures the letter's main purpose.""",
                
                DocumentType.NEWSLETTER: """Extract the newsletter title or main headline.
Look for: newsletter name, main article headline, publication title.
Return the primary title, not article subtitles.""",
                
                DocumentType.REPORT: """Extract the report title or main heading.
Look for: cover page title, main heading, report subject.
Return the primary report title."""
            }
        }
        
        # Get base prompt
        prompt = base_prompts.get(task, {}).get(doc_type, 
                                               base_prompts.get(task, {}).get(DocumentType.UNKNOWN, ""))
        
        # Add examples if provided
        if examples:
            prompt += "\n\nExamples:\n"
            for example in examples[:3]:  # Limit to 3 examples
                prompt += f"Text: {example.get('text', '')}\nExtraction: {example.get('result', '')}\n\n"
        
        # Add chain-of-thought for complex tasks
        if task == TaskType.DESCRIPTION_EXTRACTION:
            prompt += "\n\nThink step by step:\n1. Identify the main topic\n2. Find key details\n3. Summarize concisely"
        
        return prompt
    
    def estimate_text_quality(self, text_segments: List[str]) -> float:
        """Estimate OCR text quality (0.0 to 1.0)"""
        full_text = " ".join(text_segments)
        
        # Quality indicators
        total_chars = len(full_text)
        if total_chars == 0:
            return 0.0
        
        # Count problematic patterns
        issues = 0
        issues += len(re.findall(r'[^\w\s\.,!?;:\-\(\)"\']', full_text))  # Strange characters
        issues += len(re.findall(r'\s{3,}', full_text))  # Excessive whitespace
        issues += len(re.findall(r'[a-z][A-Z]', full_text))  # Inconsistent casing
        issues += len(re.findall(r'\b\w{1,2}\b', full_text)) * 0.1  # Too many short words
        
        # Calculate quality score
        issue_ratio = issues / total_chars
        quality = max(0.0, min(1.0, 1.0 - issue_ratio * 10))
        
        return quality
    
    def should_use_two_pass(self, task: TaskType, confidence: float, doc_type: DocumentType) -> bool:
        """Determine if two-pass extraction is needed"""
        
        # Always use two-pass for critical low-confidence extractions
        if confidence < 0.6:
            return True
        
        # Use two-pass for complex documents with medium confidence
        if doc_type in [DocumentType.NEWSLETTER, DocumentType.REPORT] and confidence < 0.8:
            return True
        
        # Use two-pass for description tasks with medium confidence
        if task == TaskType.DESCRIPTION_EXTRACTION and confidence < 0.75:
            return True
        
        return False
    
    def record_performance(self, model_name: str, task: TaskType, 
                          processing_time: float, confidence: float):
        """Record model performance for future optimization"""
        key = f"{model_name}_{task.value}"
        
        if key not in self.performance_history:
            self.performance_history[key] = {
                'times': [],
                'confidences': [],
                'count': 0
            }
        
        history = self.performance_history[key]
        history['times'].append(processing_time)
        history['confidences'].append(confidence)
        history['count'] += 1
        
        # Keep only recent history (last 100 runs)
        if len(history['times']) > 100:
            history['times'] = history['times'][-100:]
            history['confidences'] = history['confidences'][-100:]
    
    def get_performance_stats(self, model_name: str, task: TaskType) -> Dict:
        """Get performance statistics for model-task combination"""
        key = f"{model_name}_{task.value}"
        
        if key not in self.performance_history:
            return {'avg_time': 0, 'avg_confidence': 0, 'count': 0}
        
        history = self.performance_history[key]
        return {
            'avg_time': sum(history['times']) / len(history['times']) if history['times'] else 0,
            'avg_confidence': sum(history['confidences']) / len(history['confidences']) if history['confidences'] else 0,
            'count': history['count']
        }
