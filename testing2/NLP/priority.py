def assign_priority_by_keywords(text):
    high_priority_keywords = ['urgent', 'dangerous', 'critical', 'leaking', 'broken', 'serious']
    
    # Check for high-priority keywords
    for keyword in high_priority_keywords:
        if keyword in text.lower():
            return "High"
    
    # If no high-priority keywords are found, assign low priority
    return "Low"


'''Example
complaint = "The water pipe is leaking on the main road."
priority = assign_priority_by_keywords(complaint)
print("Keyword-Based Priority:", priority)'''
