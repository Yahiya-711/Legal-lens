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
Legal-Lens-AI/
│
├── .env                  # API keys
├── README.md
├── requirements.txt
├── app.py                # Main Streamlit app
│
├── parser_agent/
│   └── parser.py         # Handles PDF/DOCX parsing
│
├── nlp/
│   └── summarizer.py     # Handles summarization, Q&A, risk score
│
├── tts_agent/
│   └── tts.py            # gTTS logic for voice summary
│
└── ui_frontend/
    └── interface.py      # Streamlit layout, inputs, outputs

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

