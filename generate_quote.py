"""
generate_quote.py
Automatically fetches a fresh, verified quote + Hindi translation + 2-line Student Reflection
from AI based on today's theme for the "Life Mantra" series (@news.nit_iit).
"""

import json
import os
import datetime
import ai_client
import config

DAY_THEMES = {
    "Monday": {
        "theme": "Career & Ambition",
        "focus": "Placements, Careers, Discipline, Goals",
        "authors": [
            "Dr. A.P.J. Abdul Kalam",
            "Steve Jobs",
            "Elon Musk",
            "Chanakya",
            "Ratan Tata",
            "Narayana Murthy",
            "Nandan Nilekani",
            "Bill Gates",
            "Jeff Bezos",
            "Sundar Pichai",
            "Satya Nadella",
            "Indra Nooyi",
            "Warren Buffett",
            "Jack Ma",
            "Dhirubhai Ambani",
            "Azim Premji",
            "Kiran Mazumdar-Shaw",
            "Shiv Nadar",
            "Tim Cook",
            "Larry Page"
        ]
    },

    "Tuesday": {
        "theme": "Education & Learning",
        "focus": "Knowledge, Curiosity, Wisdom",
        "authors": [
            "Swami Vivekananda",
            "Dr. B.R. Ambedkar",
            "Savitribai Phule",
            "Albert Einstein",
            "Rabindranath Tagore",
            "Confucius",
            "Aristotle",
            "Socrates",
            "Plato",
            "Maria Montessori",
            "A.P.J. Abdul Kalam",
            "C.V. Raman",
            "Homi J. Bhabha",
            "Aryabhata",
            "Dr. Vikram Sarabhai",
            "Abdul Kalam Azad",
            "J. Krishnamurti",
            "Carl Sagan",
            "Richard Feynman",
            "Stephen Hawking"
        ]
    },

    "Wednesday": {
        "theme": "Resilience & Courage",
        "focus": "Failure, Persistence, Determination",
        "authors": [
            "Bhagat Singh",
            "Subhas Chandra Bose",
            "Nelson Mandela",
            "Winston Churchill",
            "Abraham Lincoln",
            "Helen Keller",
            "Malala Yousafzai",
            "Thomas Edison",
            "Michael Jordan",
            "Muhammad Ali",
            "Mary Kom",
            "Milkha Singh",
            "P.V. Sindhu",
            "Sachin Tendulkar",
            "M.S. Dhoni",
            "Virat Kohli",
            "Amitabh Bachchan",
            "J.K. Rowling",
            "Nick Vujicic",
            "Rocky Balboa (Fictional)"
        ]
    },

    "Thursday": {
        "theme": "Leadership & Character",
        "focus": "Integrity, Ethics, Vision",
        "authors": [
            "Sardar Vallabhbhai Patel",
            "Mahatma Gandhi",
            "Abraham Lincoln",
            "Atal Bihari Vajpayee",
            "Lal Bahadur Shastri",
            "Jawaharlal Nehru",
            "Nelson Mandela",
            "Martin Luther King Jr.",
            "Aung San Suu Kyi",
            "Theodore Roosevelt",
            "Lee Kuan Yew",
            "Ratan Tata",
            "Narayana Murthy",
            "Nandan Nilekani",
            "Simon Sinek",
            "Peter Drucker",
            "John C. Maxwell",
            "Shivaji Maharaj",
            "Sam Manekshaw",
            "Field Marshal Cariappa"
        ]
    },

    "Friday": {
        "theme": "Success & Innovation",
        "focus": "Innovation, Entrepreneurship, Progress",
        "authors": [
            "Nikola Tesla",
            "Bill Gates",
            "Steve Jobs",
            "Elon Musk",
            "Larry Page",
            "Sergey Brin",
            "Mark Zuckerberg",
            "Sam Altman",
            "Demis Hassabis",
            "Sundar Pichai",
            "Satya Nadella",
            "Ratan Tata",
            "Azim Premji",
            "Dr. Vikram Sarabhai",
            "Dr. A.P.J. Abdul Kalam",
            "ISRO Scientists",
            "N.R. Narayana Murthy",
            "Kailasavadivoo Sivan",
            "Thomas Edison",
            "Henry Ford"
        ]
    },

    "Saturday": {
        "theme": "Life & Mindset",
        "focus": "Growth, Happiness, Gratitude",
        "authors": [
            "Rabindranath Tagore",
            "Marcus Aurelius",
            "Stephen Hawking",
            "Mother Teresa",
            "Dalai Lama",
            "Osho",
            "Naval Ravikant",
            "Brené Brown",
            "Robin Sharma",
            "James Clear",
            "Simon Sinek",
            "Leo Tolstoy",
            "Rumi",
            "Khalil Gibran",
            "Thich Nhat Hanh",
            "Wayne Dyer",
            "Eckhart Tolle",
            "Louise Hay",
            "Sri Sri Ravi Shankar",
            "Sadhguru"
        ]
    },

    "Sunday": {
        "theme": "Peace & Reflection",
        "focus": "Purpose, Spirituality, Inner Peace",
        "authors": [
            "Swami Vivekananda",
            "Gautama Buddha",
            "Mahatma Gandhi",
            "Lao Tzu",
            "Confucius",
            "Rumi",
            "Kabir",
            "Guru Nanak",
            "Ramakrishna Paramahamsa",
            "J. Krishnamurti",
            "Mother Teresa",
            "Dalai Lama",
            "Sri Aurobindo",
            "Paramahansa Yogananda",
            "Osho",
            "Sadhguru",
            "Patanjali",
            "Saint Augustine",
            "Thich Nhat Hanh",
            "Pope Francis"
        ]
    }
}

QUOTE_PROMPT = """You are a quote editor for @news.nit_iit (Indian college students & Gen Z) for the "Life Mantra" daily morning series.

Today is {day}. The theme is "{theme}" focusing on {focus}.
Preferred Authors for today: {authors}.

TASK:
1. Provide ONE famous, well-documented, verified quotation from one of the preferred authors or another highly respected historical/modern figure.
2. Provide an accurate, natural Hindi translation of the quote.
3. Write a 2-line practical "Today's Student Reflection" explaining how this Life Mantra applies to students preparing for JEE, NEET, UPSC, GATE, placements, or life.

CRITICAL RULE:
Do NOT invent fake quotes. Use only authentic, historically attributed quotations.

Do NOT pick any of these previously used quotes:
{used_quotes}

OUTPUT FORMAT (Valid JSON object only, no markdown formatting):
{{
  "quote_en": "English quote text here",
  "quote_hi": "Hindi translation text here",
  "author": "Author Name",
  "theme": "{theme}",
  "reflection": "2-line student advice here"
}}
"""


def get_history_file():
    os.makedirs("data", exist_ok=True)
    return "data/used_quotes.json"


def load_used_quotes():
    history_file = get_history_file()
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_used_quote(quote_data):
    history_file = get_history_file()
    history = load_used_quotes()
    history.append({
        "quote_en": quote_data.get("quote_en"),
        "author": quote_data.get("author"),
        "date": str(datetime.date.today())
    })
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def fetch_daily_quote():
    """Generates today's fresh quote + Hindi translation + Student Reflection."""
    today_name = datetime.datetime.now().strftime("%A")
    theme_info = DAY_THEMES.get(today_name, DAY_THEMES["Monday"])

    used_history = load_used_quotes()
    used_titles = [item.get("quote_en", "") for item in used_history[-60:]]

    prompt = QUOTE_PROMPT.format(
        day=today_name,
        theme=theme_info["theme"],
        focus=theme_info["focus"],
        authors=", ".join(theme_info["authors"]),
        used_quotes="\n".join(used_titles) if used_titles else "None"
    )

    print(f"🌅 Generating Life Mantra for {today_name} ({theme_info['theme']})...")

    try:
        response_text = ai_client.ask_ai(prompt)
        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        quote_data = json.loads(clean_text)
        save_used_quote(quote_data)
        return quote_data
    except Exception as e:
        print(f"❌ Error fetching daily quote from AI: {e}")
        return {
            "quote_en": "Arise, awake and stop not till the goal is reached.",
            "quote_hi": "उठो, जागो और तब तक मत रुको जब तक लक्ष्य प्राप्त न हो जाए।",
            "author": "Swami Vivekananda",
            "theme": theme_info["theme"],
            "reflection": "Consistency matters more than occasional bursts of motivation. Keep showing up for your exams and goals every single day."
        }


if __name__ == "__main__":
    data = fetch_daily_quote()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    