import sys
import os
import time
import re
import socket
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# Force UTF-8 for Windows Console
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

def detect_base_url():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", 5500))
        s.close()
        return "http://127.0.0.1:5500/"
    except Exception:
        return "https://lester-4-kaizen.github.io/HUB/"

BASE_URL = detect_base_url()
TOPIC_URLS = {
    # Artificial Intelligence (GfG SPA)
    'What is Artificial Intelligence?': BASE_URL + 'ai-study-hub.html',
    'What is Machine Learning?': BASE_URL + 'ai-study-hub.html',
    'What is Narrow AI?': BASE_URL + 'ai-study-hub.html',
    'Artificial General Intelligence (AGI)': BASE_URL + 'ai-study-hub.html',
    'Artificial Super Intelligence (ASI)': BASE_URL + 'ai-study-hub.html',
    'What is Generative AI?': BASE_URL + 'ai-study-hub.html',
    'Natural Language Processing (NLP)': BASE_URL + 'ai-study-hub.html',
    'Expert Systems': BASE_URL + 'ai-study-hub.html',
    'Common AI Models & When to Use Them': BASE_URL + 'ai-study-hub.html',
    'Supervised Machine Learning': BASE_URL + 'ai-study-hub.html',
    'Unsupervised Learning': BASE_URL + 'ai-study-hub.html',
    'What is Reinforcement Learning?': BASE_URL + 'ai-study-hub.html',
    
    # CS Professional Elective 4
    '📊What is Data Analytics?': BASE_URL + 'topic-e4-what-is-data-analytics.html',
    '🔍Types of Data Analytics': BASE_URL + 'topic-e4-types-of-data-analytics.html',
    '🏢Role in Organizations': BASE_URL + 'topic-e4-role-in-organizations.html',
    '⚖️Ethics & Data Use': BASE_URL + 'topic-e4-ethics-data-use.html',
    '🔄Data Analytics Lifecycle': BASE_URL + 'topic-e4-data-analytics-lifecycle.html'
}

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_choices(df):
    subjects = sorted(df['subject'].unique())
    print("\n📚  SELECT A SUBJECT:")
    for idx, sub in enumerate(subjects, 1):
        print(f"  [{idx}] {sub}")
    
    while True:
        try:
            sel = int(input("\n👉 Enter the subject number: "))
            if 1 <= sel <= len(subjects):
                selected_sub = subjects[sel - 1]
                break
            print("❌ Invalid selection. Try again.")
        except ValueError:
            print("❌ Please enter a number.")
            
    clear_terminal()
    sub_df = df[df['subject'] == selected_sub]
    topics = sorted(sub_df['topic'].unique())
    print(f"\n📖  SELECT A TOPIC FOR {selected_sub.upper()}:")
    for idx, top in enumerate(topics, 1):
        print(f"  [{idx}] {top}")
        
    while True:
        try:
            sel = int(input("\n👉 Enter the topic number: "))
            if 1 <= sel <= len(topics):
                selected_top = topics[sel - 1]
                break
            print("❌ Invalid selection. Try again.")
        except ValueError:
            print("❌ Please enter a number.")
            
    return selected_sub, selected_top

def play_quiz(csv_path="study_hub_output/quizzes.csv"):
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found.")
        return
        
    df = pd.read_csv(csv_path)
    
    while True:
        clear_terminal()
        print("═" * 60)
        print("        🎓  STUDY HUB COMPANION: INTERACTIVE PRACTICE MODE  🎓")
        print("═" * 60)
        
        subject, topic = get_choices(df)
        
        # Look up URL
        url = TOPIC_URLS.get(topic)
        if not url:
            print(f"⚠️  URL not mapped for topic: {topic}. Using home page.")
            url = BASE_URL + "home.html"
            
        is_local = "127.0.0.1" in url
        print(f"\n🚀 Opening the browser to the quiz page ({'Local Live Server' if is_local else 'Live Public Website'})...")
        print(f"🌐 Link: {url}")
        print("\n📝 INSTRUCTIONS:")
        print("  1. If it's a dynamic GfG page, click the specific topic card in the browser.")
        print("  2. Navigate to the quiz tab and start the quiz.")
        print("  3. Solve the quiz questions in the browser at your own pace!")
        print("  4. The terminal will automatically detect when you finish.")
        
        with sync_playwright() as p:
            # Open browser in headful mode (headless=False) so user can interact
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url)
            
            score_text = "N/A"
            detected = False
            
            while True:
                # 1. Check GfG Individual Topic Quiz Results
                gfg_topic_results = page.locator("#topicQuizResults")
                if gfg_topic_results.is_visible():
                    score_el = page.locator("#tqrScore")
                    if score_el.is_visible():
                        score_text = score_el.inner_text().strip()
                        detected = True
                        break

                # 2. Check GfG Global Quiz Results
                gfg_global_results = page.locator("#qmResults")
                if gfg_global_results.is_visible():
                    score_el = page.locator("#qmrScore")
                    if score_el.is_visible():
                        score_text = score_el.inner_text().strip()
                        detected = True
                        break
                        
                # 3. Check Elective 4 / Static Topic Quiz Results
                elec4_prog = page.locator("#qzProg")
                if elec4_prog.is_visible():
                    text = elec4_prog.inner_text()
                    if "Quiz Complete!" in text:
                        match = re.search(r"You scored\s+(\d+\s*/\s*\d+)", text)
                        if match:
                            score_text = match.group(1)
                        detected = True
                        break
                        
                # Wait a bit before checking again
                time.sleep(1)
                
                # Check if browser was closed by user
                if page.is_closed():
                    print("⚠️  Browser was closed before the quiz finished.")
                    break
                    
            if detected:
                print("\n🎉 quiz completed!")
                print(f"🏆 Detected Score: {score_text}")
                
                # Save screenshot of results page
                screenshot_path = f"study_hub_output/quiz_result_{int(time.time())}.png"
                page.screenshot(path=screenshot_path)
                print(f"📸 Screenshot saved to {screenshot_path}")
                
                # Append to log
                with open("quiz_history.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now()}] Subject: {subject} | Topic: {topic} | Score: {score_text}\n")
                    
            browser.close()
            
        print("\n" + "═" * 40)
        retry = input("❓ Would you like to try another subject/topic quiz? (y/n): ").strip().lower()
        if retry not in ['y', 'yes']:
            print("\n👋 Happy studying! Closing the Study Hub Companion.")
            break

if __name__ == "__main__":
    play_quiz()
