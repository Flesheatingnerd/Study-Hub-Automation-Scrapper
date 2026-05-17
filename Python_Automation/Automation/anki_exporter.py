import pandas as pd
import genanki
import os
import sys

# Force UTF-8 for Windows Console
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

def generate_anki_deck(csv_path="study_hub_output/flashcards.csv", output_path="study_hub_output/study_hub_deck.apkg"):
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)

    # Create a unique model ID and deck ID
    model_id = 1607392319
    deck_id = 2059400110

    # Define premium CSS style
    css = """
    .card {
        font-family: 'Inter', 'Nunito', sans-serif;
        font-size: 18px;
        text-align: center;
        color: #e2e8f0;
        background-color: #0f172a;
        padding: 30px;
        line-height: 1.6;
    }
    .question {
        font-size: 24px;
        font-weight: bold;
        color: #22d3ee;
        margin-bottom: 20px;
        background: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #22d3ee;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .answer {
        font-size: 20px;
        color: #f8fafc;
        margin-top: 20px;
        background: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #4ade80;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metadata {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 30px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .tag {
        display: inline-block;
        background-color: #334155;
        padding: 4px 10px;
        border-radius: 20px;
        margin-right: 5px;
    }
    hr {
        border: none;
        height: 1px;
        background-color: #334155;
        margin: 20px 0;
    }
    """

    # Define the genanki Model
    my_model = genanki.Model(
        model_id,
        'Premium Study Hub Model',
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
            {'name': 'Subject'},
            {'name': 'Topic'}
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '<div class="metadata"><span class="tag">{{Subject}}</span> <span class="tag">{{Topic}}</span></div><br><div class="question">{{Question}}</div>',
                'afmt': '{{FrontSide}}<hr id="answer"><div class="answer">{{Answer}}</div>',
            },
        ],
        css=css
    )

    # Create the Deck
    my_deck = genanki.Deck(
        deck_id,
        '📚 HUB Master Study Deck'
    )

    print(f"📖 Processing {len(df)} flashcards...")
    
    # Iterate and add notes
    for idx, row in df.iterrows():
        my_note = genanki.Note(
            model=my_model,
            fields=[str(row['question']), str(row['answer']), str(row['subject']), str(row['topic'])]
        )
        my_deck.add_note(my_note)

    # Package and save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    genanki.Package(my_deck).write_to_file(output_path)
    print(f"✅ Successfully exported Anki deck to: {output_path}")

if __name__ == "__main__":
    generate_anki_deck()
