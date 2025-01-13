from preprocess import preprocess_text
from sentiment_analysis import analyze_sentiment
from priority import assign_priority_by_keywords
from categorization import categorize_complaint

def determine_priority(sentiment, keyword_priority):
    # Check for high priority sentiment and keyword-based priority
    if sentiment['compound'] < -0.5 or keyword_priority == 'High':
        return 'High'
    # If sentiment is neutral (compound score 0) and no high-priority keywords, set as Low
    elif sentiment['compound'] == 0.0 and keyword_priority == 'Low':
        return 'Low'
    else:
        return 'Medium'


def process_complaint(text):
    # Preprocess the text
    preprocessed_text = preprocess_text(text)

    # Analyze sentiment
    sentiment, sentiment_priority = analyze_sentiment(preprocessed_text)

    # Assign priority by keywords
    keyword_priority = assign_priority_by_keywords(preprocessed_text)

    # Categorize complaint
    category = categorize_complaint(preprocessed_text)

    # Final priority (combine sentiment and keywords)
    final_priority = "High" if sentiment_priority == "High" or keyword_priority == "High" else sentiment_priority

    return {
        "Original Complaint": text,
        "Preprocessed Text": preprocessed_text,
        "Category": category,
        "Sentiment": sentiment,
        "Final Priority": final_priority
    }

if __name__ == "__main__":
    # Example complaint related to infrastructure
    #complaint = "Water is constantly leaking from the pipe It has been two days  , there is no proper action on this , this situation is very urgent ."
    complaint = "The garbage hasn't been picked up in three weeks!"
    # Process the complaint
    result = process_complaint(complaint)
    
    # Display the result
    print("\n=== Complaint Analysis Result ===")
    print(f"Original Complaint: {result['Original Complaint']}")
    print(f"Preprocessed Text: {result['Preprocessed Text']}")
    print(f"Category: {result['Category']}")
    print(f"Sentiment: {result['Sentiment']}")
    print(f"Final Priority: {result['Final Priority']}")
