"""
study_hub_scraper.py
====================
Scrapes the CS Study Hub using a headless browser (Playwright).

Structure understood:
  - home.html               → lists all subject hub pages
  - {subject}-study-hub.html / elec4.html etc → lists topic pages
  - topic-{slug}.html       → each topic has notes, flashcards, quiz ALL IN ONE PAGE

Returns structured dict keyed by subject name.
"""

import re
from bs4 import BeautifulSoup, Tag
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, Page

BASE_URL   = "https://lester-4-kaizen.github.io/HUB/"
HOME_URL   = BASE_URL + "home.html"
WAIT_MS    = 2500

# Known subject hub pages (from inspection of the site)
SUBJECT_HUBS = [
    {"name": "Artificial Intelligence",              "url": BASE_URL + "ai.html"},
    {"name": "Automata Theory",                      "url": BASE_URL + "automata.html"},
    {"name": "Methods of Research",                  "url": BASE_URL + "research.html"},
    {"name": "Modeling and Simulation",              "url": BASE_URL + "modeling.html"},
    {"name": "Software Engineering 2",               "url": BASE_URL + "se2.html"},
    {"name": "CS Professional Elective 3",           "url": BASE_URL + "elec3.html"},
    {"name": "CS Professional Elective 4",           "url": BASE_URL + "elec4.html"},
]


def fetch(page: Page, url: str):
    """Load a page with JS rendering, return BeautifulSoup."""
    try:
        page.goto(url, timeout=20000)
        page.wait_for_timeout(WAIT_MS)
        page.wait_for_load_state("networkidle")
        return BeautifulSoup(page.content(), "html.parser")
    except Exception as e:
        print(f"    ❌ {url}  ({e})")
        return None


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_404(soup: BeautifulSoup) -> bool:
    """Detect GitHub Pages 404 pages."""
    title = soup.find("title")
    if title and "404" in title.get_text():
        return True
    body = clean(soup.get_text())
    return "does not contain the requested file" in body


def discover_topic_links(hub_soup: BeautifulSoup, page: Page, hub_url: str, subj_name: str) -> list:
    """From a subject hub page, collect all topic page links."""
    topics = []
    seen = set()

    # 1. Try to evaluate the global 'topics' array from JS (loads GfG topics only for Artificial Intelligence)
    if "Artificial Intelligence" in subj_name:
        try:
            js_topics = page.evaluate("() => typeof topics !== 'undefined' ? topics : []")
            if js_topics:
                for t in js_topics:
                    t_url = t.get("url", "")
                    if t_url:
                        full = urljoin(hub_url, t_url)
                        if full not in seen:
                            seen.add(full)
                            topics.append({
                                "name": t.get("name", t.get("shortName", t_url)),
                                "url":  full
                            })
        except Exception as e:
            print(f"      ⚠️  Error evaluating JS topics: {e}")

    # 2. Add physical <a> links from the DOM (loads Finals Reference & Elec4 topics)
    for a in hub_soup.find_all("a", href=True):
        href = str(a["href"])
        full = urljoin(hub_url, href)
        # Topic pages follow the pattern: topic-*.html
        if "topic-" in href and full not in seen:
            seen.add(full)
            label = clean(a.get_text())
            topics.append({"name": label or href, "url": full})

    return topics


def parse_topic_page(soup: BeautifulSoup, page: Page, subject: str, topic_name: str) -> dict:
    """
    Parse a single topic page which contains notes, flashcards, and quiz.
    Returns {"notes": [...], "flashcards": [...], "quiz": [...]}
    """
    notes, flashcards, quiz = [], [], []

    # ── NOTES ────────────────────────────────────────────────────────────────
    # Everything under h3/h4 headings + paragraphs + list items = reading notes
    current_section = topic_name
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li", "td"]):
        text = clean(tag.get_text())
        if not text or len(text) < 4:
            continue
        # Skip nav/UI chrome text
        if any(skip in text for skip in [
            "Flip Card", "Next →", "← Prev", "Start Quiz", "Mark as Read",
            "tap to reveal", "Click to reveal", "Back to", "All Topics",
            "Reading Notes", "Flashcards", "Quiz", "Sub-Topics", "← Restart",
            "Retry", "Exit", "Close", "CONCEPT", "EXPLANATION", "QUESTION", "ANSWER"
        ]):
            continue

        if tag.name in ("h2", "h3", "h4", "h5"):
            current_section = text
        elif tag.name in ("p", "li", "td") and len(text) > 10:
            notes.append({
                "subject":  subject,
                "topic":    topic_name,
                "section":  current_section,
                "type":     tag.name,
                "content":  text,
            })

    # ── FLASHCARDS ───────────────────────────────────────────────────────────
    # Try to extract via Playwright JS evaluation first (100% robust for dynamically defined data)
    try:
        js_fc = page.evaluate("() => typeof _fc !== 'undefined' ? _fc : []")
    except Exception:
        js_fc = []

    if js_fc:
        for i, item in enumerate(js_fc):
            flashcards.append({
                "subject":      subject,
                "topic":        topic_name,
                "card_number":  i + 1,
                "question":     clean(item.get("q", "")),
                "answer":       clean(item.get("a", "")),
            })
    else:
        # Fallback to DOM scraping
        card_containers = soup.find_all(class_=re.compile(r"card|flash|flip", re.I))
        if card_containers:
            for i, card in enumerate(card_containers):
                texts = [clean(t.get_text()) for t in card.find_all(["p","div","span","h3","h4","li"])
                         if clean(t.get_text()) and len(clean(t.get_text())) > 4]
                # Remove UI strings
                ui = {"CONCEPT","EXPLANATION","Flip","Next","Prev","tap to reveal","Click to reveal"}
                texts = [t for t in texts if t not in ui and not t.startswith("←") and not t.startswith("→")]
                texts = list(dict.fromkeys(texts))  # deduplicate
                if len(texts) >= 2:
                    flashcards.append({
                        "subject":      subject,
                        "topic":        topic_name,
                        "card_number":  i + 1,
                        "question":     texts[0],
                        "answer":       texts[1],
                    })
        else:
            # Fallback: look for dt/dd pairs
            for i, (dt, dd) in enumerate(zip(soup.find_all("dt"), soup.find_all("dd"))):
                flashcards.append({
                    "subject":     subject,
                    "topic":       topic_name,
                    "card_number": i + 1,
                    "question":    clean(dt.get_text()),
                    "answer":      clean(dd.get_text()),
                })

    # ── QUIZ ─────────────────────────────────────────────────────────────────
    # Try to extract via Playwright JS evaluation (100% robust since questions are dynamically rendered from JS)
    try:
        js_qq = page.evaluate("() => typeof _qq !== 'undefined' ? _qq : []")
    except Exception:
        js_qq = []

    if js_qq:
        for i, item in enumerate(js_qq):
            options = item.get("options", [])
            correct_idx = item.get("answer")
            correct_val = ""
            if isinstance(correct_idx, int) and 0 <= correct_idx < len(options):
                correct_val = options[correct_idx]
            elif isinstance(correct_idx, str):
                correct_val = correct_idx

            quiz.append({
                "subject":         subject,
                "topic":           topic_name,
                "question_number": i + 1,
                "question":        clean(item.get("q", "")),
                "choices":         " | ".join(clean(opt) for opt in options),
                "correct_answer":  clean(correct_val),
            })
    else:
        # Fallback to DOM parsing
        q_containers = soup.find_all(class_=re.compile(r"question", re.I))
        for i, qel in enumerate(q_containers):
            q_text = clean(qel.get_text())
            if not q_text or len(q_text) < 5:
                continue
            options, correct = [], None
            for opt in qel.find_all(class_=re.compile(r"option|choice|answer", re.I)):
                t = clean(opt.get_text())
                if t:
                    options.append(t)
                classes = " ".join(opt.get("class") or []).lower()
                if "correct" in classes:
                    correct = t
            quiz.append({
                "subject":         subject,
                "topic":           topic_name,
                "question_number": i + 1,
                "question":        q_text[:200],
                "choices":         " | ".join(options),
                "correct_answer":  correct or "",
            })

    return {"notes": notes, "flashcards": flashcards, "quiz": quiz}


def scrape() -> dict:
    """
    Main scrape function.
    Returns dict: { subject_name: { notes:[...], flashcards:[...], quiz:[...] } }
    """
    results = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page    = browser.new_page()

        # Try to discover hubs from home page first, fall back to known list
        print("  Loading home page...")
        home_soup = fetch(page, HOME_URL)

        hubs = SUBJECT_HUBS  # always use known list as base
        if home_soup and not is_404(home_soup):
            # Try to pick up any extra subject links from home
            extra_seen = {h["url"] for h in hubs}
            for a in home_soup.find_all("a", href=True):
                href = str(a["href"])
                full = urljoin(HOME_URL, href)
                if (full.startswith(BASE_URL) and
                    full.endswith(".html") and
                    "home" not in href and
                    "index" not in href and
                    full not in extra_seen):
                    extra_seen.add(full)

        print(f"  Scraping {len(hubs)} subject hub(s)...\n")

        for hub in hubs:
            subj_name = hub["name"]
            hub_url   = hub["url"]
            print(f"  📚 {subj_name}")

            hub_soup = fetch(page, hub_url)
            if not hub_soup or is_404(hub_soup):
                print(f"      ⚠️  Hub page not found: {hub_url}")
                results[subj_name] = {"notes": [], "flashcards": [], "quiz": []}
                continue

            topics = discover_topic_links(hub_soup, page, hub_url, subj_name)
            print(f"      Found {len(topics)} topic(s)")

            subj_notes, subj_fc, subj_quiz = [], [], []

            for topic in topics:
                t_name = topic["name"][:60]
                t_url  = topic["url"]
                t_soup = fetch(page, t_url)
                if not t_soup or is_404(t_soup):
                    print(f"        ⚠️  404: {t_url}")
                    continue

                parsed = parse_topic_page(t_soup, page, subj_name, t_name)
                subj_notes.extend(parsed["notes"])
                subj_fc.extend(parsed["flashcards"])
                subj_quiz.extend(parsed["quiz"])
                print(f"        ✅ {t_name[:50]}  "
                      f"(notes:{len(parsed['notes'])} fc:{len(parsed['flashcards'])} q:{len(parsed['quiz'])})")

            results[subj_name] = {
                "notes":      subj_notes,
                "flashcards": subj_fc,
                "quiz":       subj_quiz,
            }
            print(f"      Totals → notes:{len(subj_notes)}  flashcards:{len(subj_fc)}  quiz:{len(subj_quiz)}\n")

        browser.close()

    return results
