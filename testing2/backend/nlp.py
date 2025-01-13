# models/nlp.py

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer

# Download necessary NLTK resources
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('vader_lexicon')


def preprocess_text(text):
    """
    Preprocesses the complaint text by:
    - Lowercasing
    - Tokenizing
    - Removing stopwords
    - Lemmatizing
    """
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(tokens)


def categorize_complaint(text):
    """
    Categorizes the complaint based on predefined keywords and returns the associated department and category.
    """
    categories = {
        "Sanitation": ["garbage", "trash", "waste", "overflowing"],
        "Water Supply": ["water", "leak", "pipe", "drain"],
        "Infrastructure": ["road", "pothole", "bridge", "broken"],
        "Public Safety": ["crime", "dangerous", "theft", "safety"]
    }

    # Mapping categories to departments and their respective IDs
    category_to_department = {
        "Sanitation": ("Sanitation", 1),
        "Water Supply": ("Water", 2),
        "Infrastructure": ("Infrastructure", 3),
        "Public Safety": ("Safety", 4)
    }

    for category, keywords in categories.items():
        if any(keyword in text.lower() for keyword in keywords):
            return category_to_department[category]  # Return both department name and department ID

    return ("General", 5)  # Default category and department for general complaints


def assign_priority(text):
    """
    Assigns priority to the complaint text based on:
    - Keywords in the complaint
    - Sentiment analysis
    """
    # Priority based on predefined keywords
    high_priority_keywords = ['urgent', 'dangerous', 'critical', 'leaking', 'broken', 'serious']
    for keyword in high_priority_keywords:
        if keyword in text.lower():
            return "High"
    
    # Sentiment-based priority assignment
    sentiment, sentiment_priority = analyze_sentiment(text)
    
    # Return sentiment-based priority if no keyword priority is found
    if sentiment_priority == "High":
        return "High"
    elif sentiment_priority == "Medium":
        return "Medium"
    else:
        return "Low"


def analyze_sentiment(text):
    """
    Analyzes sentiment of the complaint text and assigns priority.
    """
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores(text)
    
    if sentiment['compound'] == 0.0:
        priority = "Low"
    elif sentiment['compound'] < -0.5:
        priority = "High"
    elif -0.5 <= sentiment['compound'] <= 0.5:
        priority = "Medium"
    else:
        priority = "Low"
    
    return sentiment, priority


def process_complaint(text):
    """
    Processes the complaint text by:
    - Preprocessing the text
    - Categorizing the complaint
    - Assigning priority based on sentiment and keywords
    """
    # Preprocess the text
    preprocessed_text = preprocess_text(text)

    # Categorize complaint
    category = categorize_complaint(preprocessed_text)

    # Assign priority (keywords and sentiment)
    final_priority = assign_priority(preprocessed_text)

    # Analyze sentiment (optional, for reporting purposes)
    sentiment, _ = analyze_sentiment(preprocessed_text)

    return {
        "Original Complaint": text,
        "Preprocessed Text": preprocessed_text,
        "Category": category,
        "Sentiment": sentiment,
        "Final Priority": final_priority
    }
