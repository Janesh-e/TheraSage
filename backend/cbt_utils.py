# Simple keyword-based distortion recognizer (expandable or replaceable by LLM later)
def detect_cognitive_distortion(text: str) -> str:
    text = text.lower()
    if "always" in text or "never" in text:
        return "black-and-white thinking"
    if "everything will go wrong" in text or "i’ll fail":
        return "catastrophizing"
    if "it's all my fault" in text:
        return "personalization"
    if "i can’t do anything right" in text:
        return "overgeneralization"
    return "none"

def suggest_cbt_tool(distortion: str) -> str:
    tools = {
        "black-and-white thinking": (
            "It seems like you're viewing things in extremes. "
            "Try asking: 'Is there a middle ground here?' or "
            "'Can I think of exceptions to this thought?'"
        ),
        "catastrophizing": (
            "You're imagining the worst possible outcome. Try this: "
            "'What’s the most likely outcome, realistically?' or "
            "'If the worst did happen, what could I do to cope?'"
        ),
        "personalization": (
            "You're blaming yourself for something that may not be in your control. "
            "Try: 'What evidence do I have that it's truly my fault?'"
        ),
        "overgeneralization": (
            "You’re drawing broad conclusions from one event. "
            "Ask: 'What specific facts support this conclusion?' or "
            "'Is there another way to look at this experience?'"
        ),
        "none": "I didn't detect any cognitive distortions, but if you'd like, I can help guide you through a reflection anyway."
    }
    return tools.get(distortion, tools["none"])

def run_cbt_analysis(text: str) -> dict:
    distortion = detect_cognitive_distortion(text)
    tool_suggestion = suggest_cbt_tool(distortion)
    return {
        "distortion": distortion,
        "cbt_tool": tool_suggestion
    }
