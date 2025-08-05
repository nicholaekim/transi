#!/usr/bin/env python3
"""
Smart Document Analyzer - Intelligent text segmentation and structure analysis
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TextSegmentType(Enum):
    HEADER = "header"
    TITLE = "title"
    DATE = "date"
    BODY = "body"
    SIGNATURE = "signature"
    METADATA = "metadata"
    UNKNOWN = "unknown"

@dataclass
class TextSegment:
    """Enhanced text segment with metadata"""
    content: str
    segment_type: TextSegmentType
    confidence: float
    line_number: int
    char_position: int
    
class SmartDocumentAnalyzer:
    """Intelligent document structure analysis and segmentation"""
    
    def __init__(self):
        self.date_patterns = [
            r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',  # MM/DD/YYYY, MM-DD-YY
            r'\b\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}\b',    # YYYY/MM/DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
        ]
        
        self.title_indicators = [
            r'^[A-Z][A-Z\s]{5,50}$',  # ALL CAPS titles
            r'^[A-Z][a-zA-Z\s]{10,80}$',  # Title case
            r'^\s*(?:Re:|Subject:|Title:)\s*(.+)$',  # Explicit subject lines
        ]
        
        self.signature_patterns = [
            r'\b(?:Sincerely|Best regards|Yours truly|Cordially|Respectfully)\b',
            r'\b(?:Signed|Signature|Name)\s*:',
            r'^\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s*$'  # Name pattern
        ]
        
        self.metadata_patterns = [
            r'\b(?:Volume|Vol\.?)\s*\d+',
            r'\b(?:Issue|No\.?)\s*\d+',
            r'\b(?:Page|P\.?)\s*\d+',
            r'\b(?:Edition|Ed\.?)\s*\d+'
        ]
    
    def analyze_document_structure(self, text: str) -> Dict[str, any]:
        """Analyze overall document structure and characteristics"""
        lines = text.split('\n')
        
        analysis = {
            'total_lines': len(lines),
            'total_chars': len(text),
            'avg_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0,
            'has_headers': False,
            'has_signatures': False,
            'has_metadata': False,
            'estimated_type': 'unknown',
            'structure_confidence': 0.5
        }
        
        # Analyze line characteristics
        short_lines = sum(1 for line in lines if len(line.strip()) < 20)
        long_lines = sum(1 for line in lines if len(line.strip()) > 80)
        
        # Check for various document elements
        full_text = text.lower()
        
        # Header detection
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in self.title_indicators[:2]):
            analysis['has_headers'] = True
        
        # Signature detection
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in self.signature_patterns):
            analysis['has_signatures'] = True
        
        # Metadata detection
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in self.metadata_patterns):
            analysis['has_metadata'] = True
        
        # Document type estimation
        if 'dear' in full_text and analysis['has_signatures']:
            analysis['estimated_type'] = 'letter'
            analysis['structure_confidence'] = 0.8
        elif analysis['has_metadata'] or 'newsletter' in full_text:
            analysis['estimated_type'] = 'newsletter'
            analysis['structure_confidence'] = 0.7
        elif 'report' in full_text or 'analysis' in full_text:
            analysis['estimated_type'] = 'report'
            analysis['structure_confidence'] = 0.7
        
        return analysis
    
    def segment_text_intelligently(self, text: str) -> List[TextSegment]:
        """Intelligently segment text based on structure analysis"""
        lines = text.split('\n')
        segments = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            segment_type = self._classify_line(line, i, lines)
            confidence = self._estimate_segment_confidence(line, segment_type)
            char_pos = text.find(line)
            
            segments.append(TextSegment(
                content=line,
                segment_type=segment_type,
                confidence=confidence,
                line_number=i,
                char_position=char_pos
            ))
        
        return segments
    
    def _classify_line(self, line: str, line_num: int, all_lines: List[str]) -> TextSegmentType:
        """Classify a single line based on content and context"""
        
        # Date detection
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.date_patterns):
            return TextSegmentType.DATE
        
        # Title detection (usually early in document)
        if line_num < 5:  # First 5 lines
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.title_indicators):
                return TextSegmentType.TITLE
            if len(line) > 10 and line[0].isupper() and line.count(' ') < 8:
                return TextSegmentType.TITLE
        
        # Header detection
        if line_num < 3 or (len(line) < 50 and line.isupper()):
            return TextSegmentType.HEADER
        
        # Signature detection (usually at end)
        if line_num > len(all_lines) - 10:  # Last 10 lines
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.signature_patterns):
                return TextSegmentType.SIGNATURE
        
        # Metadata detection
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.metadata_patterns):
            return TextSegmentType.METADATA
        
        # Default to body
        return TextSegmentType.BODY
    
    def _estimate_segment_confidence(self, line: str, segment_type: TextSegmentType) -> float:
        """Estimate confidence in segment classification"""
        base_confidence = 0.6
        
        if segment_type == TextSegmentType.DATE:
            # Strong patterns get higher confidence
            if re.search(r'\d{4}-\d{2}-\d{2}', line):
                return 0.9
            elif re.search(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', line):
                return 0.8
        
        elif segment_type == TextSegmentType.TITLE:
            if line.isupper() and 10 <= len(line) <= 60:
                return 0.8
            elif line[0].isupper() and line.count(' ') < 8:
                return 0.7
        
        elif segment_type == TextSegmentType.SIGNATURE:
            if any(word in line.lower() for word in ['sincerely', 'regards', 'yours']):
                return 0.9
        
        return base_confidence
    
    def get_segments_by_type(self, segments: List[TextSegment], 
                           segment_type: TextSegmentType) -> List[TextSegment]:
        """Get all segments of a specific type"""
        return [seg for seg in segments if seg.segment_type == segment_type]
    
    def get_contextual_segments(self, segments: List[TextSegment], 
                              target_type: TextSegmentType, 
                              context_lines: int = 2) -> List[str]:
        """Get segments with surrounding context for better extraction"""
        target_segments = self.get_segments_by_type(segments, target_type)
        
        if not target_segments:
            # If no specific segments found, return relevant sections
            if target_type == TextSegmentType.TITLE:
                # Return first few segments
                return [seg.content for seg in segments[:5]]
            elif target_type == TextSegmentType.DATE:
                # Return header and first few segments
                headers = self.get_segments_by_type(segments, TextSegmentType.HEADER)
                first_few = segments[:3]
                return [seg.content for seg in headers + first_few]
            elif target_type == TextSegmentType.SIGNATURE:
                # Return last few segments
                return [seg.content for seg in segments[-5:]]
        
        # Return target segments with context
        result = []
        for target in target_segments:
            start_idx = max(0, target.line_number - context_lines)
            end_idx = min(len(segments), target.line_number + context_lines + 1)
            
            context_segments = segments[start_idx:end_idx]
            result.extend([seg.content for seg in context_segments])
        
        return result
    
    def create_optimized_segments_for_task(self, text: str, task_type: str) -> List[str]:
        """Create optimized text segments for specific extraction tasks"""
        segments = self.segment_text_intelligently(text)
        
        if task_type == "title":
            # Focus on headers and early content
            title_segments = self.get_contextual_segments(segments, TextSegmentType.TITLE)
            header_segments = self.get_contextual_segments(segments, TextSegmentType.HEADER)
            return list(set(title_segments + header_segments))  # Remove duplicates
        
        elif task_type == "date":
            # Focus on date segments and headers
            date_segments = self.get_contextual_segments(segments, TextSegmentType.DATE)
            header_segments = self.get_contextual_segments(segments, TextSegmentType.HEADER)
            return list(set(date_segments + header_segments))
        
        elif task_type == "description":
            # Focus on body content, avoid headers and signatures
            body_segments = self.get_segments_by_type(segments, TextSegmentType.BODY)
            return [seg.content for seg in body_segments[:10]]  # First 10 body segments
        
        elif task_type == "volume_issue":
            # Focus on metadata and headers
            metadata_segments = self.get_contextual_segments(segments, TextSegmentType.METADATA)
            header_segments = self.get_contextual_segments(segments, TextSegmentType.HEADER)
            return list(set(metadata_segments + header_segments))
        
        else:
            # Default: return all segments
            return [seg.content for seg in segments]
    
    def get_document_quality_metrics(self, text: str) -> Dict[str, float]:
        """Analyze document quality for processing optimization"""
        
        metrics = {
            'text_clarity': 0.0,
            'structure_clarity': 0.0,
            'completeness': 0.0,
            'overall_quality': 0.0
        }
        
        if not text:
            return metrics
        
        # Text clarity (OCR quality indicators)
        total_chars = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        space_chars = sum(1 for c in text if c.isspace())
        punct_chars = sum(1 for c in text if c in '.,!?;:')
        
        # Good text should be mostly alphabetic with reasonable spacing
        if total_chars > 0:
            alpha_ratio = alpha_chars / total_chars
            space_ratio = space_chars / total_chars
            punct_ratio = punct_chars / total_chars
            
            metrics['text_clarity'] = min(1.0, alpha_ratio + space_ratio * 2 + punct_ratio * 5)
        
        # Structure clarity
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            avg_line_length = sum(len(line) for line in lines) / len(lines)
            line_length_variance = sum((len(line) - avg_line_length) ** 2 for line in lines) / len(lines)
            
            # Good structure has reasonable line lengths and variance
            metrics['structure_clarity'] = min(1.0, (avg_line_length / 100) * (1 - line_length_variance / 10000))
        
        # Completeness (presence of expected elements)
        has_beginning = len(text) > 100
        has_end = text.strip().endswith(('.', '!', '?', '"')) or len(text) > 500
        has_structure = len(lines) > 3
        
        completeness_score = sum([has_beginning, has_end, has_structure]) / 3
        metrics['completeness'] = completeness_score
        
        # Overall quality
        metrics['overall_quality'] = (
            metrics['text_clarity'] * 0.4 +
            metrics['structure_clarity'] * 0.3 +
            metrics['completeness'] * 0.3
        )
        
        return metrics
