# PDF Metadata Extraction Pipeline

A comprehensive PDF metadata extraction system with interactive batch processing and web interface.

## 📁 Project Structure

```
ocr3.0/
├── 📁 src/                          # Source code
│   ├── 📁 core/                     # Core pipeline logic
│   │   ├── __init__.py
│   │   └── pipeline.py              # Main PDF processing pipeline
│   ├── 📁 utils/                    # Utility scripts
│   │   ├── __init__.py
│   │   └── data_checker.py          # Interactive batch processor
│   └── 📁 web/                      # Web application
│       ├── __init__.py
│       ├── app.py                   # Flask web app
│       └── 📁 templates/            # HTML templates
│           └── index.html
├── 📁 data/                         # Data storage
│   ├── 📁 raw/                      # Input PDFs for batch processing
│   ├── 📁 processed/                # Processed files
│   ├── 📁 results/                  # Batch processing results
│   └── feedback_memory.json        # User feedback and fine-tuning data
├── 📁 config/                       # Configuration files

## 📊 Extracted Metadata

- **Title**: Document title or main subject
- **Date**: Publication or creation date
- **Description**: Intelligent summary of content
- **Volume/Issue**: Publication volume and issue numbers
- **Confidence Scores**: Reliability metrics for each extraction
- **Processing Metadata**: Performance analytics and model details

## ⚡ Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install and start Ollama:**
   ```bash
   # Install Ollama (macOS)
   brew install ollama
   
   # Start Ollama service
   ollama serve
   ```

3. **Install required models:**
   ```bash
   ollama pull granite3.2-vision
   ollama pull llama3.1:8b
   ollama pull llama3.1:70b
   ```

4. **Configure Transkribus API (Optional - for PDF processing):**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your Transkribus credentials
   # Get credentials from: https://transkribus.eu/
   ```

## 🚀 Quick Start

### Process PDF (with Transkribus API)
```bash
# Process PDF through Transkribus OCR
python3 simple_pipeline.py document.pdf

# This will:
# 1. Upload PDF to Transkribus
# 2. Run OCR processing
# 3. Save extracted text for manual correction
# 4. Prompt you to review and correct the text
# 5. Re-run with corrected text file
```

### Process Text File (already corrected)
```bash
# Process pre-corrected text file
python3 simple_pipeline.py document.txt
```

## 🎯 Usage Modes

### **Parallel Mode (Default - Fastest)**
```bash
python3 simple_pipeline.py document.txt
python3 simple_pipeline.py document.txt --priority speed
```

### **Consensus Mode (Highest Accuracy)**
```bash
python3 simple_pipeline.py document.txt --mode consensus --priority accuracy
```

### **Custom Processing**
```bash
# Skip automatic feedback
python3 simple_pipeline.py document.txt --no-feedback

# Balance speed and accuracy
python3 simple_pipeline.py document.txt --priority balanced
```

## 🔄 Complete Workflow

1. **📄 Transkribus Processing**: Upload document → OCR → Manual correction → Export as `.txt`
2. **🧠 Document Analysis**: Automatic type detection and quality assessment
3. **⚡ Parallel Extraction**: Simultaneous processing of all metadata fields
4. **🎯 Quality Validation**: Confidence scoring and optional two-pass extraction
5. **💾 Results Storage**: Structured JSON with detailed metadata
6. **📊 Automatic Feedback**: Accuracy analysis and improvement suggestions

## 📁 Clean Project Structure

```
ocr/
├── simple_pipeline.py                    # 🚀 Main advanced pipeline
├── fine_tune_and_train.py                # 📊 Feedback & training system
├── src/core/
│   ├── enhanced_extractor.py             # 🤖 Advanced LLM extraction
│   ├── smart_document_analyzer.py        # 📋 Document analysis & segmentation
│   └── advanced_model_manager.py         # 🧠 Intelligent model selection
├── end_pipeline/                         # 📁 Final results (JSON)
├── training_data/                        # 📚 Feedback & improvement data
└── requirements.txt                      # 📦 Minimal dependencies
```

## 🎛️ Advanced Options

| Option | Description | Values |
|--------|-------------|--------|
| `--mode` | Extraction strategy | `parallel` (fast), `consensus` (accurate) |
| `--priority` | Processing priority | `speed`, `balanced`, `accuracy` |
| `--no-feedback` | Skip feedback analysis | flag |

## 📈 Performance Features

- **4x Faster**: Parallel processing vs sequential
- **Smart Caching**: Document type and performance caching
- **Dynamic Routing**: Optimal model selection per task
- **Quality Adaptation**: Processing adjusts to text quality
- **Continuous Improvement**: Learning from user corrections

## 🔧 Requirements

- Python 3.8+
- Ollama with models: `granite3.2-vision`, `llama3.1:8b`, `llama3.1:70b`
- 8GB+ RAM recommended for optimal performance

## 📊 Output Format

Results include enhanced metadata:
```json
{
  "title": "Document Title",
  "date": "2024-01-15",
  "description": "Intelligent summary...",
  "volume_issue": "Volume 3, Issue 2",
  "extraction_metadata": {
    "total_processing_time": 2.34,
    "extraction_method": "parallel",
    "field_details": {
      "title": {
        "confidence": 0.92,
        "model_used": "granite3.2-vision",
        "processing_time": 0.58
      }
    }
  },
  "document_analysis": {
    "document_type": "newsletter",
    "quality": {"overall_quality": 0.87}
  }
}
```
