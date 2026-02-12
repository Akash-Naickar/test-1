# ContextSync: Institutional Memory as a Service

**ContextSync** bridges the gap between your code and your team's knowledge. It uses a RAG (Retrieval-Augmented Generation) pipeline to connect your IDE directly to your Slack conversations and Jira tickets.

## 🚀 Features
*   **"Explain Intent"**: Highlights code and explains *why* it exists based on historical context.
*   **"Context Cards"**: Surfaces raw Slack threads and Jira tickets related to your code.
*   **"Institutional Memory"**: Prevents you from repeating past mistakes by surfacing forgotten warnings.

## 🛠️ Tech Stack
*   **Extension**: VS Code (TypeScript)
*   **Backend**: FastAPI (Python)
*   **AI Engine**: Google Gemini 1.5 Pro
*   **Vector DB**: ChromaDB

## 📦 Installation

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. VS Code Extension
```bash
cd vscode-extension
npm install
npm run compile
# Press F5 in VS Code to launch the Extension Host
```

## 🎥 Demo
Check out the `demo/` folder for a self-contained scenario demonstrating the "Idempotency Key" bug.

## 🤝 Contributing
1.  Fork the repo
2.  Create your feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit your changes (`git commit -m 'Add some amazing feature'`)
4.  Push to the branch (`git push origin feature/amazing-feature`)
5.  Open a Pull Request
