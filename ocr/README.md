# OCR Pipeline v3.0

🚀 **Advanced metadata extraction pipeline with Transkribus integration**

Clean, organized pipeline for extracting structured metadata from documents using AI models and professional OCR.

## 📁 Project Structure

```
ocr/
├── run_pipeline.py          # Main entry point
├── requirements.txt         # Dependencies
├── .env                    # Environment variables (create from config/.env.example)
│
├── pipeline/               # Core pipeline code
│   ├── simple_pipeline.py  # Main pipeline logic
│   ├── core/              # Core modules
│   │   ├── advanced_model_manager.py
│   │   ├── enhanced_extractor.py
│   │   ├── smart_document_analyzer.py
│   │   └── transkribus_client.py
│   └── utils/             # Utilities
│       └── fine_tune_and_train.py
│
├── config/                # Configuration files
│   └── .env.example       # Environment template
│
├── scripts/               # Setup and testing scripts
│   ├── setup.sh          # Automated setup
│   └── test_workflow.py   # Testing utilities
│
├── data/                  # Data directories
│   ├── input/            # Input documents
│   ├── output/           # Final results
│   └── temp/             # Temporary files
│
└── docs/                 # Documentation
    └── README.md         # This file
```

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
   cp config/.env.example .env
   
   # Edit .env with your Transkribus credentials
   # Get credentials from: https://transkribus.eu/
   ```

## 🚀 Quick Start

### Process PDF (with Transkribus API)
```bash
# Process PDF through Transkribus OCR
python3 run_pipeline.py document.pdf

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
python3 run_pipeline.py document.txt
```

## 🎯 Usage Modes

### Parallel Mode (Default - Fastest)
```bash
python3 run_pipeline.py document.txt --mode parallel
```

### Consensus Mode (Highest Accuracy)
```bash
python3 run_pipeline.py document.txt --mode consensus
```

### Priority Settings
```bash
# Speed optimized
python3 run_pipeline.py document.txt --priority speed

# Balanced (default)
python3 run_pipeline.py document.txt --priority balanced

# Accuracy optimized
python3 run_pipeline.py document.txt --priority accuracy
```

## 📊 Features

- **🤖 Advanced AI Models**: Multiple specialized LLMs for different tasks
- **📄 PDF Processing**: Transkribus integration for professional OCR
- **🔄 Two-Pass Extraction**: Consensus validation for accuracy
- **📈 Smart Document Analysis**: Automatic quality assessment and optimization
- **🎯 Dynamic Model Selection**: Task-specific model routing
- **📝 Manual Correction**: Human-in-the-loop workflow
- **🔧 Automatic Feedback**: Continuous improvement system
- **⚡ Parallel Processing**: Fast multi-field extraction
- **📋 Confidence Scores**: Reliability metrics for each extraction
- **🎛️ Processing Metadata**: Performance analytics and model details

## 🛠️ Automated Setup

```bash
# Run automated setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## 🧪 Testing

```bash
# Run test workflow
python3 scripts/test_workflow.py

# Test with sample document
python3 run_pipeline.py data/temp/sample_document.txt
```

## 📤 Output

Results are saved to `data/output/end_results.json` with:
- **Extracted Metadata**: Title, date, description, volume/issue
- **Confidence Scores**: Reliability metrics
- **Processing Details**: Model performance and timing
- **Document Analysis**: Quality metrics and structure info

## 🔧 Advanced Options

```bash
# Skip automatic feedback analysis
python3 run_pipeline.py document.txt --no-feedback

# Full help
python3 run_pipeline.py --help
```

## 📚 Workflow

1. **Input**: PDF or text file
2. **OCR** (if PDF): Transkribus processing
3. **Manual Correction**: Review extracted text
4. **AI Processing**: Multi-model metadata extraction
5. **Validation**: Consensus checking and confidence scoring
6. **Output**: Structured JSON with metadata
7. **Feedback**: Automatic accuracy analysis and improvement

---

**Built with advanced AI models and professional OCR for maximum accuracy and reliability.**
