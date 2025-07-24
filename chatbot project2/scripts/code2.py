import sqlite3
import random
from datetime import datetime
import nltk
from nltk.chat.util import Chat, reflections
from tkinter import *
from tkinter.scrolledtext import ScrolledText
import json
from difflib import get_close_matches
import spacy
import threading

# Download NLTK data (first-time setup)
nltk.download('punkt')

# Load spaCy for better NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("spaCy English model not found. Please install with: python -m spacy download en_core_web_sm")
    nlp = None

# Set up SQLite database with better structure
conn = sqlite3.connect('mentalhealth_chatbot.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables with improved schema
cursor.execute('''
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    bot_response TEXT,
    sentiment_score REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMIME
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    last_session DATETIME
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    url TEXT,
    category TEXT
)
''')

conn.commit()

# Load knowledge base from JSON file
def load_knowledge_base(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"questions": []}

knowledge_base = load_knowledge_base('knowledge_base.json')

# Save to knowledge base
def save_knowledge_base(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

# Find closest matching question
def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

# Enhanced response system
class EnhancedMentalHealthChatbot:
    def __init__(self):
        self.pairs = self._load_response_patterns()
        self.chatbot = Chat(self.pairs, reflections)
        self.resources = self._load_resources()
        self.user_context = {}
        
    def _load_response_patterns(self):
        """Load response patterns with more nuanced mental health support"""
        return [
            [
                r"(.*) feeling (sad|depressed|lonely|down|exhausted|hopeless)(.*)",
                ["I'm really sorry you're feeling %2. That sounds really difficult. Would you like to share more about what's going on?", 
                 "I hear that you're feeling %2. That must be really hard. I'm here to listen if you want to talk about it."]
            ],
            [
                r"(.*) (stress|anxiety|stressed|anxious|panic|overwhelmed)(.*)",
                ["%2 can feel really overwhelming. Remember to breathe - you're doing great by reaching out. What specifically is causing your %2?",
                 "I understand %2 can be really challenging. Would it help to talk through what's bothering you?"]
            ],
            [
                r"(.*) (happy|good|great|awesome|wonderful)(.*)",
                ["I'm so glad you're feeling %2! It's wonderful to hear that. What's contributing to these positive feelings?",
                 "That's fantastic that you're feeling %2! Would you like to share what's bringing you joy?"]
            ],
            [
                r"(.*) (burden|useless|worthless|stupid|not enough|failure)(.*)",
                ["I want you to know that your feelings are valid, but I'm concerned that you're being so hard on yourself. Would you talk to me more about why you feel this way?",
                 "Hearing you say that makes me want to remind you that you matter. These thoughts can be really painful. Would you like to share what's going on?"]
            ],
            [
                r"(.*) (suicide|end it all|kill myself|don't want to live)(.*)",
                ["I'm really concerned about what you're saying. Your life is valuable. Please reach out to a crisis hotline immediately. In the US, you can call 988 for the Suicide & Crisis Lifeline. Would you like me to help you find local resources?",
                 "I hear how much pain you're in right now. Please know you're not alone. Can I help you connect with someone who can provide more support?"]
            ],
            [
                r"(.*) (help me|need help|support)(.*)",
                ["I'm here to help. Can you tell me more about what kind of support you're looking for?",
                 "I want to provide the right kind of support. What would be most helpful for you right now?"]
            ],
            [
                r"(.*) (cope|coping|deal with)(.*)",
                ["Coping with difficult emotions can be challenging. Some strategies include deep breathing, talking to someone you trust, or engaging in a calming activity. What usually helps you when you're struggling?",
                 "Finding healthy ways to cope is so important. Would you like some suggestions for coping strategies that might help?"]
            ],
            [
                r"(.*) (angry|frustrated|annoyed|irritated|mad)(.*)",
                ["I hear that you're feeling %2. It's okay to feel this way. Would you like to talk about what's causing these feelings?",
                 "Feeling %2 can be really tough. Sometimes taking deep breaths or stepping away for a moment helps. What's bothering you?"]
            ],
            [
                r"(.*) (scared|afraid|fearful|terrified)(.*)",
                ["It sounds like you're feeling %2. Fear can be overwhelming. You're safe here—would you like to share what's frightening you?",
                "I'm here with you while you feel %2. Would it help to talk through what's scaring you?"]
            ],
            [
                r"(.*) (lonely|isolated|alone)(.*)",
                ["Feeling %2 can be so painful. You're not alone—I'm here to listen. Would you like to talk about what's happening?",
                "I hear your loneliness. Would it help to connect with someone you trust? You matter."]
            ],
            [
                r"(.*) (confused|uncertain|lost)(.*)",
                ["Feeling %2 is understandable when things are unclear. Let's try to sort this out together. What's on your mind?",
                "It's okay to feel %2. Sometimes writing things down helps. Would you like to explore this more?"]
            ],
            [
                r"(.*) (grateful|thankful|appreciative)(.*)",
                ["It's wonderful that you're feeling %2! Gratitude can be so healing. What are you thankful for today?",
                "Celebrating these %2 feelings with you! Would you like to share what brought this on?"]
            ],
            [   
                r"(.*) (numb|empty|detached)(.*)",
                ["Feeling %2 can be really disorienting. You're not alone in this. Would you like to talk about what's happening?",
                "I hear that you're feeling %2. Sometimes our minds do this to protect us. Would it help to explore this together?"]
            ],
            [
                r"(.*)",
                ["I'm listening carefully. Can you tell me more about how you're feeling?",
                 "I hear you. How is this affecting you?"]
            ]
        ]
        
    
    def _load_resources(self):
        """Load mental health resources from database"""
        cursor.execute("SELECT * FROM resources")
        return cursor.fetchall()
    
    def analyze_sentiment(self, text):
        """Basic sentiment analysis (would be better with a proper NLP library)"""
        positive_words = ['happy', 'good', 'great', 'awesome', 'better', 'improved']
        negative_words = ['sad', 'depressed', 'anxious', 'bad', 'terrible', 'hopeless']
        
        score = 0
        words = text.lower().split()
        for word in words:
            if word in positive_words:
                score += 1
            elif word in negative_words:
                score -= 1
                
        return score
    
    def respond(self, user_input):
        """Generate a response with context awareness"""
        # First check knowledge base
        best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])
        if best_match:
            answer = self._get_answer_for_question(best_match)
            if answer:
                return answer
        
        # Then check pattern responses
        response = self.chatbot.respond(user_input)
        
        # If no good response, generate a thoughtful follow-up
        if not response or response == "None":
            follow_ups = [
                "I want to make sure I understand. Can you explain that in another way?",
                "I'm listening carefully. What else is on your mind?",
                "That's important. How has this been affecting you?",
                "glad you could share that. What would be helpful for you right now?"
            ]
            response = random.choice(follow_ups)
        
        # Log sentiment
        sentiment = self.analyze_sentiment(user_input)
        self._log_conversation(user_input, response, sentiment)
        
        return response
    
    def _get_answer_for_question(self, question):
        for q in knowledge_base["questions"]:
            if q["question"] == question:
                return q["answer"]
        return None
    
    def _log_conversation(self, user_input, bot_response, sentiment_score):
        cursor.execute('''
        INSERT INTO conversations (user_input, bot_response, sentiment_score) 
        VALUES (?, ?, ?)
        ''', (user_input, bot_response, sentiment_score))
        conn.commit()
    
    def suggest_resources(self, category=None):
        """Suggest mental health resources based on conversation context"""
        if category:
            cursor.execute("SELECT * FROM resources WHERE category=?", (category,))
            resources = cursor.fetchall()
        else:
            resources = self.resources
        
        if resources:
            return random.choice(resources)
        return None

class ChatUI:
    def __init__(self, master):
        self.master = master
        master.title("Mental Health Support Chatbot")
        master.geometry("600x700")
        master.configure(bg='#f0f8ff')
        
        # Create enhanced chatbot
        self.chatbot = EnhancedMentalHealthChatbot()
        
        # Header
        header = Label(master, text="Mental Health Support", font=('Arial', 16, 'bold'), bg='#f0f8ff', fg='#2c3e50')
        header.pack(pady=10)
        
        # Chat display
        self.chat_display = ScrolledText(master, wrap=WORD, width=70, height=25, font=('Arial', 12))
        self.chat_display.tag_config('user', foreground='#3498db', font=('Arial', 12, 'bold'))
        self.chat_display.tag_config('bot', foreground='#2ecc71', font=('Arial', 12))
        self.chat_display.tag_config('resource', foreground='#e74c3c', font=('Arial', 12, 'italic'))
        self.chat_display.pack(pady=10, padx=10)
        
        # Input frame
        input_frame = Frame(master, bg='#f0f8ff')
        input_frame.pack(pady=10)
        
        self.user_input = Entry(input_frame, width=60, font=('Arial', 12))
        self.user_input.pack(side=LEFT, padx=5)
        self.user_input.bind("<Return>", self.send_message)
        self.user_input.focus_set()
        
        send_btn = Button(input_frame, text="Send", command=self.send_message, 
                         bg='#3498db', fg='white', font=('Arial', 10, 'bold'))
        send_btn.pack(side=LEFT)
        
        # Emergency button
        emergency_btn = Button(master, text="Emergency Resources", command=self.show_resources,
                             bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'))
        emergency_btn.pack(pady=5)
        
        # Initial bot message
        self.display_message("bot", "Hello, I'm here to listen and support you. How are you feeling today?")
    
    def display_message(self, sender, message, resource=False):
        tag = 'user' if sender == 'user' else 'resource' if resource else 'bot'
        prefix = "You: " if sender == 'user' else "Support Bot: "
        self.chat_display.insert(END, prefix + message + "\n\n", tag)
        self.chat_display.see(END)
        
    def send_message(self, event=None):
        user_input = self.user_input.get().strip()
        if not user_input:
            return
            
        if user_input.lower() == 'quit':
            self.display_message("bot", "Thank you for chatting. Remember to be kind to yourself. You can always come back if you need to talk.")
            self.master.after(2000, self.master.destroy)
            return
        
        self.display_message("user", user_input)
        self.user_input.delete(0, END)
        
        # Process response in a separate thread to keep UI responsive
        threading.Thread(target=self.process_response, args=(user_input,), daemon=True).start()
    
    def process_response(self, user_input):
        # Get bot response
        bot_response = self.chatbot.respond(user_input)
        
        # Display after a short delay to simulate typing
        self.master.after(500, lambda: self.display_message("bot", bot_response))
        
        # Check if we should suggest resources
        if random.random() < 0.3:  # 30% chance to suggest a resource
            resource = self.chatbot.suggest_resources()
            if resource:
                self.master.after(1500, lambda: self.display_message("bot", 
                    f"Here's a resource that might help: {resource[1]}\n{resource[3]}", resource=True))
    
    def show_resources(self):
        """Show emergency mental health resources"""
        resources = [
            ("National Suicide Prevention Lifeline (US)", "Call 988", "https://988lifeline.org"),
            ("Crisis Text Line", "Text HOME to 741741", "https://www.crisistextline.org"),
            ("International Association for Suicide Prevention", "Find resources worldwide", "https://www.iasp.info/resources/Crisis_Centres/"),
            ("Mental Health America", "Find local resources", "https://www.mhanational.org")
        ]
        
        india_resources = [
            ("Vandrevala Foundation", "Call +91 9999 666 555 (24/7)", "https://www.vandrevalafoundation.com"),
            ("iCall Helpline", "Call +91 91529 87821 (Mon-Sat, 10AM-8PM)", "https://icallhelpline.org"),
            ("AASRA (Suicide Prevention)", "Call +91 98204 66766 (24/7)", "http://www.aasra.info"),
            ("National Mental Health Helpline", "Call 1800-599-0019 (24/7)", "https://www.nimhans.ac.in"),
            ("Fortis Stress Helpline", "Call +91 83768 04102 (24/7)", "https://www.fortishealthcare.com")
        ]
    
        self.display_message("bot", "🚨 Here are emergency resources in India:")
        for title, desc, url in india_resources:
            self.display_message("bot", f"{title}: {desc}\n{url}", resource=True)
        
        self.display_message("bot", "🚨 Here are some important resources globalwise:")
        for title, desc, url in resources:
            self.display_message("bot", f"{title}: {desc}\n{url}", resource=True)
            
    def initialize_resources():
        
        cursor.execute("SELECT COUNT(*) FROM resources")
        if cursor.fetchone()[0] == 0:
            resources = [
                # Crisis Helplines (India)
                ("Vandrevala Foundation", "24/7 Mental Health Helpline: Call +91 9999 666 555", "https://www.vandrevalafoundation.com", "crisis"),
                ("iCall", "Psychosocial helpline (Mon-Sat, 10AM-8PM): +91 91529 87821", "https://icallhelpline.org", "crisis"),
                ("COOJ Mental Health Foundation", "Helpline for Goa: +91 98225 25200", "https://cooj.co.in", "crisis"),
                
                # Therapy & Counseling (India)
                ("The Mind Clinic", "Online therapy sessions (Pan-India)", "https://themindclan.com", "therapy"),
                ("InnerHour", "Self-care app with Indian therapists", "https://www.theinnerhour.com", "therapy"),
                ("Manas", "Free counseling by TISS students", "https://www.tiss.edu/manas", "therapy"),
                
                # Self-Help (India)
                ("Let's Talk About Mental Health", "Hindi/English mental health guides", "https://letstalkaboutmentalhealth.com.in", "self-help"),
                ("The Health Collective", "Mental health stories & resources", "https://www.thehealthcollective.in", "education"),
                
                # LGBTQ+ Support (India)
                ("Sangath", "Mental health support for LGBTQ+", "https://sangath.in", "lgbtq"),
                ("Nazariya", "Queer-affirmative counseling", "http://nazariyaqfrg.tumblr.com", "lgbtq"),
                
                #more links(global)
                ("National Suicide Prevention Lifeline", "24/7 free and confidential support", "https://988lifeline.org", "crisis"),
                ("Crisis Text Line", "Text HOME to 741741 for 24/7 crisis support", "https://www.crisistextline.org", "crisis"),
                ("Mindfulness Exercises", "Guided mindfulness and meditation exercises", "https://www.mindful.org/free-mindfulness-resources/", "self-help"),
                ("7 Cups", "Free online therapy and counseling", "https://www.7cups.com", "therapy"),
                ("Anger Management", "Healthy ways to process anger", "https://www.apa.org/topics/anger/control", "anger"),
                ("Anxiety UK", "Support for anxiety and fear", "https://www.anxietyuk.org.uk", "fear"),
                ("The Friendship Bench", "Combat loneliness", "https://friendshipbenchzimbabwe.org", "loneliness"),
                ("Emotional Numbness Guide", "Understanding detachment", "https://www.healthline.com/health/emotional-numbness", "numbness")
            ]
            cursor.executemany('''
            INSERT INTO resources (title, description, url, category)
            VALUES (?, ?, ?, ?)
            ''', resources)
            conn.commit()
            print("Resources database initialized")
        else:
            print("Resources already exist in database")

    # Initialize resources
    initialize_resources()

# Run the application
if __name__ == "__main__":
    root = Tk()
    chat_app = ChatUI(root)
    
    # Set window icon and minimum size
    try:
        root.iconbitmap('chatbot_icon.ico')
    except:
        pass
    root.minsize(500, 600)
    
    root.mainloop()
    conn.close()