from transformers import pipeline

# Load the emotion detection pipeline once
emotion_classifier = pipeline("text-classification",
                              model="j-hartmann/emotion-english-distilroberta-base",
                              return_all_scores=True)

def detect_emotion(text: str):
    predictions = emotion_classifier(text)[0]
    sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)
    top = sorted_predictions[0]
    return {
        "emotion": top['label'],
        "confidence": round(top['score'], 4)
    }
