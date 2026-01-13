# 🔬 RxLens: Intelligent Medication Awareness System

<div align="center">

**An AI-powered, offline-capable clinical decision support tool for medication interaction analysis**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CrewAI](https://img.shields.io/badge/Powered%20by-CrewAI-orange.svg)](https://www.crewai.com/)

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation)

</div>

---

## 📋 Overview

RxLens is a sophisticated command-line application that leverages multi-agent AI systems to analyze potential medication interactions and provide evidence-based risk assessments. Designed with a focus on **educational awareness** rather than prescriptive guidance, RxLens helps healthcare students, researchers, and informed patients understand medication combinations through natural language processing and structured clinical reasoning.

### 🎯 Core Philosophy

- **Educational, Not Prescriptive**: Provides awareness information, never medical advice
- **Offline-First Architecture**: Operates independently with minimal API dependencies
- **Ethical AI Framework**: Built-in safety checks and non-diagnostic language enforcement
- **Professional Output**: Enterprise-grade terminal UI with structured data presentation

---

## ✨ Features

### 🤖 Multi-Agent AI Architecture
- **5-Stage Sequential Analysis Pipeline**:
  1. **Interpreter Agent**: Normalizes and validates medication input
  2. **Interaction Agent**: Identifies pharmacological overlap and interaction vectors
  3. **Risk Agent**: Assesses severity levels with confidence scoring
  4. **Translator Agent**: Converts technical findings to plain English
  5. **Ethics Agent**: Ensures educational framing and removes prescriptive language

### 📊 Professional Interface
- **Real-time Progress Tracking**: Visual progress bars with stage indicators
- **Structured ASCII Tables**: Clean, aligned data presentation with Unicode box drawing
- **Color-Coded Risk Levels**: Intuitive severity visualization (✓ SAFE, ⚠️ CAUTION, ⛔ AVOID)
- **Confidence Scoring**: Transparent uncertainty communication (high, medium, limited_data)
- **Key Findings Summary**: Quick-glance analysis highlights with bullet points
- **Timestamp Tracking**: Analysis provenance for record-keeping

### 🔍 Analysis Capabilities
- Detects pharmacokinetic and pharmacodynamic interactions
- Identifies shared metabolic pathways (CYP enzymes, transporters)
- Assesses additive/synergistic effects
- Provides mechanism-specific explanations (e.g., "Both NSAIDs inhibit COX enzymes")
- Confidence-weighted recommendations

### 🛡️ Safety & Ethics
- Automatic medical disclaimer insertion
- Removal of diagnostic/action-oriented phrasing
- Preservation of medication names (prevents generic substitution errors)
- Educational language enforcement

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                           │
│                    (Comma-separated meds)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: INTERPRETER AGENT                                  │
│  • Normalize medication names                                │
│  • Validate input format                                     │
│  • Extract structured medication list                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: INTERACTION AGENT                                  │
│  • Detect pharmacological overlaps                           │
│  • Identify shared vectors (enzyme inhibition, etc.)         │
│  • Generate interaction descriptions                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: RISK AGENT                                         │
│  • Assess severity levels (safe/caution/avoid)               │
│  • Calculate confidence scores                               │
│  • Provide clinical context                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: TRANSLATOR AGENT                                   │
│  • Convert technical language to plain English               │
│  • Preserve specific mechanisms and medication names         │
│  • Ensure accessibility for non-experts                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 5: ETHICS AGENT                                       │
│  • Remove prescriptive/diagnostic language                   │
│  • Enforce educational tone                                  │
│  • Add medical disclaimers                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Formatted Output                          │
│         (Structured tables + key findings)                   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **AI Framework** | CrewAI | Multi-agent orchestration |
| **LLM Backend** | Groq (Llama 3.3 70B) | Natural language reasoning |
| **Data Validation** | Pydantic | Schema enforcement |
| **Terminal UI** | Colorama + Unicode | Professional visual output |
| **Testing** | Pytest | Unit/integration testing |
| **Language** | Python 3.10+ | Core runtime |

---

## 📦 Installation

### Prerequisites
- **Python**: 3.10 or higher
- **API Key**: Groq API key ([Get one free](https://console.groq.com/))
- **OS**: Windows, macOS, or Linux

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rxlens.git
   cd rxlens
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Create .env file
   echo GROQ_API_KEY=your_api_key_here > .env
   ```

5. **Run RxLens**
   ```bash
   python app.py
   ```

---

## 🚀 Usage

### Basic Analysis

```bash
$ python app.py

╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                              RxLens: Medication Awareness Tool                                                     ║
║                              Offline • Educational • Non-Prescriptive                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

Enter medications (comma-separated):
Example: aspirin, ibuprofen, vitamin-d
> aspirin, warfarin
```

### Sample Output

```
📊 Summary: 1 interaction(s) • Risk: ⚠️ CAUTION

► Medications Analyzed
────────────────────────────────────────────────────────────────────────────
  1. Aspirin
  2. Warfarin

💡 Key Findings
────────────────────────────────────────────────────────────────────────────
  • ⚠️ Interaction: aspirin, warfarin - Both medications thin the blood
  • ⚠️ Risk: May increase bleeding risk when combined

► Detected Interactions
╔════╦══════════════════════════════════╦════════════════════════════════╦═══════════════╗
║ #  │ Substances                        │ Description                     │ Confidence    ║
╠════╬══════════════════════════════════╬════════════════════════════════╬═══════════════╣
║ 1  │ aspirin, warfarin                 │ Both are anticoagulants that   │ high          ║
║    │                                   │ may increase bleeding risk      │               ║
╚════╩══════════════════════════════════╩════════════════════════════════╩═══════════════╝
```

### Advanced Usage

**Exit Application**
```
> q
```

**Continuous Analysis**
Enter multiple medication sets in succession without restarting the application.

---

## 📂 Project Structure

```
rxlens/
├── app.py                      # Main CLI entry point
├── requirements.txt            # Python dependencies
├── .env                        # API configuration (not tracked)
├── README.md                   # This file
├── IMPLEMENTATION_SUMMARY.md   # Technical implementation notes
│
├── agents/                     # AI agent definitions
│   ├── __init__.py
│   ├── interpreter.py          # Input normalization agent
│   ├── interaction.py          # Interaction detection agent
│   ├── risk.py                 # Risk assessment agent
│   ├── translator.py           # Plain-language translation agent
│   └── ethics.py               # Safety & ethics enforcement agent
│
├── models/                     # Data models & schemas
│   ├── __init__.py
│   └── medication.py           # Pydantic models (Medication, Interaction, RiskLayer, AnalysisResult)
│
├── knowledge/                  # Offline knowledge base
│   └── rxlens_knowledge_pack.json
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   └── loader.py               # Knowledge base loader
│
└── tests/                      # Test suite
    ├── __init__.py
    └── test_agents.py          # Agent unit tests
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Groq API Key
GROQ_API_KEY=gsk_your_api_key_here

# Optional: Model Selection
GROQ_MODEL=llama-3.3-70b-versatile

# Optional: Logging
LOG_LEVEL=ERROR
```

### Customization

**Modify Risk Thresholds** ([app.py](app.py))
```python
RISK_COLORS = {
    "safe": Fore.GREEN + "✓ SAFE" + Style.RESET_ALL,
    "caution": Fore.YELLOW + "⚠️ CAUTION" + Style.RESET_ALL,
    "avoid": Fore.RED + "⛔ AVOID" + Style.RESET_ALL
}
```

**Adjust Agent Verbosity** ([agents/*.py](agents/))
```python
agent = Agent(
    role="...",
    goal="...",
    backstory="...",
    verbose=False  # Set to True for debugging
)
```

---

## 🧪 Testing

### Run Test Suite
```bash
pytest tests/ -v
```

### Test Coverage
```bash
pytest --cov=agents --cov=models tests/
```

### Manual Testing
```bash
# Test with known interaction
python app.py
> fluoxetine, tramadol

# Test with safe combination
python app.py
> vitamin-c, vitamin-d

# Test with single medication
python app.py
> aspirin
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Follow PEP 8** style guidelines
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Commit with clear messages** (`git commit -m 'Add: Feature description'`)
7. **Push to your branch** (`git push origin feature/AmazingFeature`)
8. **Open a Pull Request**

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run linter
flake8 agents/ models/ utils/ app.py

# Format code
black agents/ models/ utils/ app.py
```

---

## 🔒 Disclaimer

**IMPORTANT MEDICAL DISCLAIMER**

RxLens is an **educational tool** designed for awareness and learning purposes only. It is **NOT** a substitute for professional medical advice, diagnosis, or treatment.

- ❌ Do not use for clinical decision-making
- ❌ Do not replace consultations with healthcare providers
- ❌ Not validated for patient care
- ❌ Not FDA-approved or clinically endorsed

**Always consult qualified healthcare professionals** before making any medication decisions.

---

## 📄 License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2026 RxLens Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **CrewAI** - Multi-agent framework enabling sophisticated AI collaboration
- **Groq** - High-performance LLM inference infrastructure
- **Colorama** - Cross-platform terminal color support
- **Pydantic** - Robust data validation and serialization
- **Open-source community** - For inspiration and tools

---

## 📧 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/rxlens/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/rxlens/discussions)
- **Email**: your.email@example.com

---

## 🗺️ Roadmap

### Planned Features
- [ ] Web UI (Flask/FastAPI + React frontend)
- [ ] Docker containerization
- [ ] Export to PDF/JSON reports
- [ ] Analysis history database
- [ ] Drug class detection (NSAID, SSRI, etc.)
- [ ] Batch processing mode
- [ ] REST API endpoints
- [ ] Internationalization (i18n)

### Research Extensions
- [ ] Integration with FAERS database
- [ ] Machine learning confidence scoring
- [ ] Evidence-based citation system
- [ ] Clinical trial reference linking

---

<div align="center">

**Built with ❤️ for safer medication awareness**

⭐ Star this repo if you find it helpful!

</div>