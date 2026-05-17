# 🎓 CS Study Hub Automation System

A premium, production-grade Python automation suite designed to scrape, compile, and interact with the **CS Study Hub** platform. 

This system provides a full-circle learning cycle: automatically scraping study content (notes, cards, quizzes), typesetting a high-fidelity printable study book, building interactive Anki flashcard decks, and serving as a real-time console companion that tracks your scores as you practice in your web browser!

---

## 🛠️ Prerequisites & Setup

To run this suite, your machine needs **Python 3.8+** installed. Follow these quick steps to set up all dependencies:

### 1. Install Required Python Packages
Open your terminal inside the project directory and run:
```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers
Playwright requires its browser binaries to run. Install them by running:
```bash
playwright install
```

### 3. Start Your Local Web Server
If you are developing locally, make sure your **Live Server** (e.g., the VS Code Live Server extension) is running at:
👉 `http://127.0.0.1:5500/`

---

## 📂 Project Structure

```text
Automation/
├── study_hub_scraper.py  # Core web crawler (Playwright + BeautifulSoup)
├── report_generator.py   # Statistical Report Lab generator
├── main.py               # Orchestrator (scrapes the site, saves CSVs, builds statistics PDF)
├── quiz_player.py        # Interactive study companion (Playwright-backed score tracker)
├── anki_exporter.py      # Beautiful Anki Flashcard deck compiler (.apkg)
├── study_guide_pdf.py    # Multi-page typesetting engine (generates the Master Study Guide PDF)
└── study_hub_output/     # Generated exports directory
    ├── notes.csv         # Structured raw reading notes
    ├── flashcards.csv    # Structured raw flashcards
    ├── quizzes.csv       # Structured raw multiple-choice questions
    ├── full_export.json  # Complete hierarchical structural database
    ├── study_hub_deck.apkg # Ready-to-import Anki Deck (with custom dark-mode CSS)
    └── master_study_guide.pdf # Fully typeset printable Study Book with answers
```

---

## 🚀 How to Run the Tools

### 1. Scrape & Sync Database (`main.py`)
Fetches notes, cards, and quizzes from all active subject hubs. Generates the database CSVs and a statistics report PDF.
```bash
python main.py
```

### 2. Interactive Study & Quiz Companion (`quiz_player.py`)
An elite practice companion. You pick a subject and topic, and it:
* Opens the Chromium browser automatically to your local live server.
* Waits silently as you manually solve the quiz in the browser at your own pace.
* Dynamically detects when you finish, extracts your final score, takes a screenshot of the victory screen, and logs the session to `quiz_history.log`!
```bash
python quiz_player.py
```

### 3. Generate Anki Flashcard Decks (`anki_exporter.py`)
Converts the scraped flashcards into a modern Anki deck styled with high-end HSL dark-mode CSS cards.
```bash
python anki_exporter.py
```

### 4. Build the Printable Master Study Book (`study_guide_pdf.py`)
Compiles all scraped notes, flashcard tables, and multiple-choice quizzes (complete with mock exams and answer keys at the back) into a single typeset PDF book.
```bash
python study_guide_pdf.py
```

---

## 💎 Features Hand-Off Summary
*   **100% Dynamic Scraping:** Playwright evaluates client-side SPA arrays in `data.js` to extract dynamic topics, merging them with physical static anchors.
*   **Robust DOM Detection:** Built-in loops watch three different HTML schemas to detect when you finish quizzes and extract your scores with regular expressions.
*   **Custom Typesetting:** Dynamic table cells, wrap margins, headers, and colored callout highlights using ReportLab Platypus Flowables.
*   **Modern CSS Flashcards:** Custom card styles injected directly into Anki's SQLite database to make studying on mobile gorgeous and premium.
