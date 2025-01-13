def categorize_complaint(text):
    categories = {
        "Sanitation": ["garbage", "trash", "waste", "overflowing"],
        "Water Supply": ["water", "leak", "pipe", "drain"],
        "Infrastructure": ["road", "pothole", "bridge", "broken"],
        "Public Safety": ["crime", "dangerous", "theft", "safety"]
    }
    for category, keywords in categories.items():
        if any(keyword in text.lower() for keyword in keywords):
            return category
    return "General"

'''Example
complaint = "The garbage is overflowing in my street."
category = categorize_complaint(complaint)
print("Category:", category)'''
