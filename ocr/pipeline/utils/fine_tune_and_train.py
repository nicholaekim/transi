#!/usr/bin/env python3
"""
Fine-Tune and Train LLMs - Accuracy Checker and Model Improvement
Analyzes JSON output accuracy and creates training data for LLM improvement
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add pipeline core to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMFineTuner:
    """Fine-tuning and training system for OCR metadata extraction LLMs"""
    
    def __init__(self):
        self.training_data_dir = Path("training_data")
        self.feedback_dir = Path("feedback")
        self.models_dir = Path("model_improvements")
        
        # Create directories
        for dir_path in [self.training_data_dir, self.feedback_dir, self.models_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def analyze_json_accuracy(self, json_file: str, source_text_file: str = None) -> Dict:
        """Analyze the accuracy of extracted metadata in JSON file"""
        try:
            # Load JSON results
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Load source text if provided
            source_text = ""
            if source_text_file and os.path.exists(source_text_file):
                with open(source_text_file, 'r', encoding='utf-8') as f:
                    source_text = f.read()
            elif 'source_text_file' in results:
                source_file = results['source_text_file']
                if os.path.exists(source_file):
                    with open(source_file, 'r', encoding='utf-8') as f:
                        source_text = f.read()
            
            print(f"🔍 ANALYZING: {json_file}")
            print("="*60)
            
            # Analyze each field
            analysis = {
                'file': json_file,
                'timestamp': datetime.now().isoformat(),
                'fields': {},
                'overall_score': 0,
                'suggestions': []
            }
            
            # Analyze Title
            title_analysis = self._analyze_title(results.get('title', ''), source_text)
            analysis['fields']['title'] = title_analysis
            print(f"📄 TITLE: {results.get('title', 'N/A')}")
            print(f"   Confidence: {title_analysis['confidence']}/10")
            print(f"   Issues: {', '.join(title_analysis['issues']) if title_analysis['issues'] else 'None'}")
            
            # Analyze Date
            date_analysis = self._analyze_date(results.get('date', ''), source_text)
            analysis['fields']['date'] = date_analysis
            print(f"📅 DATE: {results.get('date', 'N/A')}")
            print(f"   Confidence: {date_analysis['confidence']}/10")
            print(f"   Issues: {', '.join(date_analysis['issues']) if date_analysis['issues'] else 'None'}")
            
            # Analyze Description
            desc_analysis = self._analyze_description(results.get('description', ''), source_text)
            analysis['fields']['description'] = desc_analysis
            print(f"📝 DESCRIPTION: {results.get('description', 'N/A')[:100]}...")
            print(f"   Confidence: {desc_analysis['confidence']}/10")
            print(f"   Issues: {', '.join(desc_analysis['issues']) if desc_analysis['issues'] else 'None'}")
            
            # Analyze Volume/Issue
            vol_analysis = self._analyze_volume_issue(results.get('volume_issue', ''), source_text)
            analysis['fields']['volume_issue'] = vol_analysis
            print(f"📚 VOLUME/ISSUE: {results.get('volume_issue', 'N/A')}")
            print(f"   Confidence: {vol_analysis['confidence']}/10")
            print(f"   Issues: {', '.join(vol_analysis['issues']) if vol_analysis['issues'] else 'None'}")
            
            # Calculate overall score
            total_confidence = sum(field['confidence'] for field in analysis['fields'].values())
            analysis['overall_score'] = total_confidence / len(analysis['fields'])
            
            print("="*60)
            print(f"🎯 OVERALL ACCURACY SCORE: {analysis['overall_score']:.1f}/10")
            
            # Generate improvement suggestions
            analysis['suggestions'] = self._generate_suggestions(analysis)
            if analysis['suggestions']:
                print("💡 IMPROVEMENT SUGGESTIONS:")
                for i, suggestion in enumerate(analysis['suggestions'], 1):
                    print(f"   {i}. {suggestion}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_title(self, title: str, source_text: str) -> Dict:
        """Analyze title extraction accuracy"""
        issues = []
        confidence = 8  # Default confidence
        
        if not title or title.lower() in ['no title found', 'n/a']:
            issues.append("No title extracted")
            confidence = 2
        elif title.startswith('"') and title.endswith('"'):
            # Good - properly quoted
            confidence = 9
        elif len(title) > 200:
            issues.append("Title too long - may include description")
            confidence = 6
        elif len(title) < 10:
            issues.append("Title too short - may be incomplete")
            confidence = 7
        
        # Check if title appears in source text
        if source_text and title.strip('"').lower() not in source_text.lower():
            issues.append("Title not found in source text")
            confidence = max(3, confidence - 3)
        
        return {
            'confidence': confidence,
            'issues': issues,
            'value': title
        }
    
    def _analyze_date(self, date: str, source_text: str) -> Dict:
        """Analyze date extraction accuracy"""
        issues = []
        confidence = 8
        
        if not date or date.lower() in ['no date found', 'n/a']:
            issues.append("No date extracted")
            confidence = 2
        elif len(date) == 4 and date.isdigit():
            # Year only - acceptable
            confidence = 7
        elif len(date) == 10 and date.count('-') == 2:
            # ISO format YYYY-MM-DD - excellent
            confidence = 10
        elif not any(char.isdigit() for char in date):
            issues.append("Date contains no numbers")
            confidence = 3
        
        # Check for reasonable date range (1900-2030)
        if date and any(char.isdigit() for char in date):
            year_candidates = [word for word in date.split() if word.isdigit() and len(word) == 4]
            if year_candidates:
                year = int(year_candidates[0])
                if year < 1900 or year > 2030:
                    issues.append(f"Unlikely year: {year}")
                    confidence = max(4, confidence - 2)
        
        return {
            'confidence': confidence,
            'issues': issues,
            'value': date
        }
    
    def _analyze_description(self, description: str, source_text: str) -> Dict:
        """Analyze description extraction accuracy"""
        issues = []
        confidence = 8
        
        if not description or description.lower() in ['no description available', 'n/a']:
            issues.append("No description extracted")
            confidence = 2
        elif len(description) < 50:
            issues.append("Description too short")
            confidence = 6
        elif len(description) > 1000:
            issues.append("Description too long - may be entire document")
            confidence = 5
        
        # Check for good summary characteristics
        if description:
            if description.count('.') < 2:
                issues.append("Description lacks sentence structure")
                confidence = max(5, confidence - 1)
            
            # Check if description contains key information from source
            if source_text:
                key_words = ['meeting', 'annual', 'general', 'vancouver', 'november', 'ctf']
                found_keywords = sum(1 for word in key_words if word.lower() in description.lower())
                if found_keywords < 2:
                    issues.append("Description missing key document details")
                    confidence = max(4, confidence - 2)
        
        return {
            'confidence': confidence,
            'issues': issues,
            'value': description
        }
    
    def _analyze_volume_issue(self, volume_issue: str, source_text: str) -> Dict:
        """Analyze volume/issue extraction accuracy"""
        issues = []
        confidence = 8
        
        if not volume_issue or volume_issue.lower() in ['no volume/issue found', 'n/a']:
            # This might be correct for letters/documents without volume/issue
            confidence = 8
        elif 'volume' in volume_issue.lower() and 'issue' in volume_issue.lower():
            # Good format
            confidence = 9
        elif volume_issue.lower().startswith('vol'):
            # Acceptable abbreviation
            confidence = 8
        else:
            issues.append("Unusual volume/issue format")
            confidence = 6
        
        return {
            'confidence': confidence,
            'issues': issues,
            'value': volume_issue
        }
    
    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        # Overall score suggestions
        if analysis['overall_score'] < 6:
            suggestions.append("Consider reviewing and correcting the source text quality")
            suggestions.append("Check if the document type matches expected format")
        
        # Field-specific suggestions
        for field, data in analysis['fields'].items():
            if data['confidence'] < 7:
                if field == 'title':
                    suggestions.append("Title LLM: Improve prompt to focus on document headers and main subjects")
                elif field == 'date':
                    suggestions.append("Date LLM: Enhance temporal reasoning and date format recognition")
                elif field == 'description':
                    suggestions.append("Description LLM: Improve summarization length and key information extraction")
                elif field == 'volume_issue':
                    suggestions.append("Volume/Issue LLM: Better recognition of publication metadata patterns")
        
        return suggestions
    
    def create_training_data(self, json_file: str, corrections: Dict = None) -> str:
        """Create training data from analysis and corrections"""
        try:
            # Load original results
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Create training entry
            training_entry = {
                'timestamp': datetime.now().isoformat(),
                'source_file': json_file,
                'original_results': results,
                'corrections': corrections or {},
                'training_prompts': {}
            }
            
            # Generate improved prompts for each field
            if corrections:
                for field, corrected_value in corrections.items():
                    if field in results and results[field] != corrected_value:
                        training_entry['training_prompts'][field] = {
                            'original_output': results[field],
                            'correct_output': corrected_value,
                            'improvement_needed': True
                        }
            
            # Save training data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            training_file = self.training_data_dir / f"training_data_{timestamp}.json"
            
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump(training_entry, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Training data saved: {training_file}")
            return str(training_file)
            
        except Exception as e:
            logger.error(f"Training data creation failed: {str(e)}")
            return ""
    
    def interactive_correction(self, json_file: str) -> Dict:
        """Interactive correction session for improving results"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            print(f"\n🔧 INTERACTIVE CORRECTION SESSION")
            print(f"File: {json_file}")
            print("="*60)
            
            corrections = {}
            
            # Title correction
            print(f"📄 Current Title: {results.get('title', 'N/A')}")
            new_title = input("Enter correct title (or press Enter to keep): ").strip()
            if new_title:
                corrections['title'] = new_title
            
            # Date correction
            print(f"📅 Current Date: {results.get('date', 'N/A')}")
            new_date = input("Enter correct date (YYYY-MM-DD format, or press Enter to keep): ").strip()
            if new_date:
                corrections['date'] = new_date
            
            # Description correction
            print(f"📝 Current Description: {results.get('description', 'N/A')[:100]}...")
            new_desc = input("Enter correct description (or press Enter to keep): ").strip()
            if new_desc:
                corrections['description'] = new_desc
            
            # Volume/Issue correction
            print(f"📚 Current Volume/Issue: {results.get('volume_issue', 'N/A')}")
            new_vol = input("Enter correct volume/issue (or press Enter to keep): ").strip()
            if new_vol:
                corrections['volume_issue'] = new_vol
            
            if corrections:
                # Create training data
                training_file = self.create_training_data(json_file, corrections)
                print(f"✅ Corrections saved to training data: {training_file}")
            else:
                print("ℹ️ No corrections made")
            
            return corrections
            
        except Exception as e:
            logger.error(f"Interactive correction failed: {str(e)}")
            return {}
    
    def generate_improvement_report(self) -> str:
        """Generate a comprehensive improvement report"""
        try:
            report_file = self.models_dir / f"improvement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            # Analyze all training data
            training_files = list(self.training_data_dir.glob("*.json"))
            
            report_content = f"""# LLM Improvement Report
Generated: {datetime.now().isoformat()}

## Summary
- Total training sessions: {len(training_files)}
- Training data files analyzed: {len(training_files)}

## Field-Specific Analysis

### Title Extraction
- Common issues: Needs better header recognition
- Suggested improvements: Focus on document structure analysis

### Date Extraction  
- Common issues: Format standardization needed
- Suggested improvements: Enhanced temporal reasoning prompts

### Description Extraction
- Common issues: Length optimization needed
- Suggested improvements: Better summarization techniques

### Volume/Issue Extraction
- Common issues: Pattern recognition for publications
- Suggested improvements: Metadata-specific training

## Recommendations

1. **Prompt Engineering**: Refine system prompts based on common error patterns
2. **Training Data**: Use collected corrections for fine-tuning
3. **Model Updates**: Consider updating to newer model versions
4. **Validation**: Implement automated accuracy checking

## Next Steps

1. Review training data in `training_data/` directory
2. Apply prompt improvements to LLM extractors
3. Test improvements with new documents
4. Continue feedback collection
"""
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"📊 Improvement report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return ""

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fine-Tune and Train LLMs for OCR Metadata Extraction')
    parser.add_argument('json_file', help='JSON results file to analyze')
    parser.add_argument('--interactive', action='store_true', help='Run interactive correction session')
    parser.add_argument('--report', action='store_true', help='Generate improvement report')
    parser.add_argument('--source-text', help='Source text file for analysis')
    
    args = parser.parse_args()
    
    fine_tuner = LLMFineTuner()
    
    if args.report:
        fine_tuner.generate_improvement_report()
    elif args.interactive:
        analysis = fine_tuner.analyze_json_accuracy(args.json_file, args.source_text)
        if analysis.get('overall_score', 0) < 8:
            print(f"\n⚠️ Low accuracy score ({analysis['overall_score']:.1f}/10). Running interactive correction...")
            fine_tuner.interactive_correction(args.json_file)
    else:
        analysis = fine_tuner.analyze_json_accuracy(args.json_file, args.source_text)
        
        if analysis.get('overall_score', 0) < 7:
            print(f"\n🔧 Would you like to run interactive correction? (y/n): ", end="")
            if input().lower().startswith('y'):
                fine_tuner.interactive_correction(args.json_file)

if __name__ == "__main__":
    main()
