# 🔍 LEGAL-LENS AI

LEGAL-LENS AI is an intelligent assistant for simplifying and understanding complex legal documents. Built for a hackathon by a team of 4, this project helps users **upload, summarize, and listen to legal documents**, making legal language more accessible and less overwhelming.

Many users blindly accept terms & agreements by clicking “I Agree” without reading the fine print. **Legal-Lens AI** helps bridge that gap.

---

## 🚀 Features

- 📄 **Document Upload:** Upload PDF or DOCX legal files.
- 🧠 **AI Summarization:** Uses DeepSeek API to summarize legal content clearly.
- 🔊 **Voice Response:** Converts summaries into spoken audio using Google Text-to-Speech (gTTS).
- ⚡ **Simple UI:** Streamlit-based frontend for a clean, fast user experience.
- 📦 **Modular Backend:** Agents-based architecture for separation of concerns.

---

## 🧩 Tech Stack

| Area              | Tool/Library              |
|-------------------|---------------------------|
| Frontend UI       | Streamlit                 |
| PDF Parsing       | `pdfminer.six`            |
| DOCX Parsing      | `python-docx`, `docx2txt` |
| Summarization     | DeepSeek API              |
| Voice Synthesis   | gTTS, pydub               |
| Backend Utility   | Python 3.10+, requests    |
| Orchestration     | Custom modular structure  |

---

## 🗂️ Project Folder Structure
```
LEGAL-LENS-AI/
│
├── README.md
├── requirements.txt
├── main.py                       # Main orchestrator or Streamlit app
├── config.py                    # API keys and constants
│
├── assets/                      # Static files
│   ├── sample_docs/             # Example PDFs or DOCX for testing
│   └── audio_outputs/           # Generated MP3 files
│
├── parser_agent/                # Member 1
│   ├── _init_.py
│   ├── parser.py                # PDF/DOCX parsing logic
│   └── utils.py                 # Helper functions (cleaning, etc.)
│
├── summarizer_agent/           # Member 2
│   ├── _init_.py
│   ├── summarizer.py            # DeepSeek or LLM summarization logic
│   └── chunker.py               # Optional: Break long text into chunks
│
├── tts_agent/                  # Member 3
│   ├── _init_.py
│   ├── tts.py                   # GTTS text-to-speech logic
│   └── audio_utils.py           # Audio cleanup, caching
│
├── ui_frontend/                # Member 4
│   ├── _init_.py
│   ├── interface.py             # Streamlit or Flask frontend
│   └── display.py               # UI logic for summary/audio

```

---

## 🛠️ Installation & Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/Yahiya-711/legal-lens.git
cd legal-lens
```

### 2. Install dependencies: Make sure you have Python 3.10+ installed.
```pip install -r requirements.txt```

### 3. Set up configuration: Create a config.py file in the root with the following:
```DEEPSEEK_API_KEY = "your-deepseek-api-key" ```

### 4. Run the application:
```streamlit run main.py```

# 📌 Example Use Case
1. Upload a legal agreement PDF (e.g., Terms & Conditions).
2. The app parses the document.
3. Summary is generated using AI.
4. Click “Play” to listen to the summary.

