"""
Guardrail checks for the healthcare chatbot.

These run before the answer is generated. is_emergency and is_off_topic
let the graph short circuit and return a safe canned message instead of
calling the model, so an emergency or an unrelated question does not
depend on the model behaving correctly on its own.
"""

DISCLAIMER = (
    "This chatbot gives general health information only. It does not "
    "provide medical diagnosis and is not a replacement for advice from a "
    "qualified healthcare professional. In an emergency, contact local "
    "emergency services or go to the nearest hospital right away."
)

# Keywords that flag a possible medical emergency.
# Kept cautious on purpose, a false positive just shows an extra safety
# message, a false negative could miss a real emergency.
EMERGENCY_KEYWORDS = [
    "chest pain",
    "cant breathe",
    "can't breathe",
    "difficulty breathing",
    "suicidal",
    "suicide",
    "want to die",
    "severe bleeding",
    "heavy bleeding",
    "unconscious",
    "not responding",
    "heart attack",
    "stroke",
    "overdose",
    "not breathing",
    "seizure",
]

EMERGENCY_MESSAGE = (
    "This sounds like it could be a medical emergency. Please contact your "
    "local emergency number or go to the nearest emergency room right now. "
    "I am not able to provide emergency medical care."
)

# Keywords for questions clearly outside the six health topics this bot
# is scoped to. Not exhaustive, just enough to catch obvious cases
# before spending an API call on them.
OFF_TOPIC_KEYWORDS = [
    "write code",
    "python script",
    "javascript",
    "stock price",
    "share market",
    "weather forecast",
    "movie recommendation",
    "song lyrics",
    "sports score",
    "election result",
    "cryptocurrency",
    "math problem",
    "recipe for",
]

OFF_TOPIC_MESSAGE = (
    "I can only help with general health topics, things like symptoms, "
    "diseases, healthy lifestyle, nutrition, preventive care, and first "
    "aid. Could you ask me something in one of those areas?"
)


def contains_emergency_signal(text):
    # simple lowercase substring check
    lowered = text.lower()
    return any(keyword in lowered for keyword in EMERGENCY_KEYWORDS)


def contains_off_topic_signal(text):
    lowered = text.lower()
    return any(keyword in lowered for keyword in OFF_TOPIC_KEYWORDS)


# greetings, thanks, and quick questions about the bot itself. these
# get a normal reply but skip the knowledge base lookup, the review
# pause, and they do not count as a real question for the download
# buttons. matched as a whole cleaned message, not a substring, so a
# real question that happens to start with "hi" is not caught by this
CASUAL_MESSAGES = {
    "hi", "hii", "hello", "hey", "yo", "hiya",
    "good morning", "good afternoon", "good evening", "good night",
    "how are you", "how are you doing", "hows it going",
    "thanks", "thank you", "thank you so much", "thanks a lot", "thankyou",
    "thx", "ty", "appreciate it", "appreciated",
    "ok", "okay", "alright", "cool", "nice", "great", "awesome",
    "got it", "understood",
    "bye", "goodbye", "bye bye", "see you", "see ya", "take care",
    "what can you do", "what can you help me with", "what can you help with",
    "who are you", "what are you", "what is this", "what do you do",
    "tell me about yourself", "introduce yourself",
}

GREETING_PREFIXES = ["hello", "hi", "hii", "hey", "yo", "hiya"]


def is_casual_message(text):
    cleaned = text.lower().strip().strip("!.?,;:")
    cleaned = " ".join(cleaned.split())

    if cleaned in CASUAL_MESSAGES:
        return True

    # allows a leading greeting before a casual phrase, so "hello what
    # can you do" still matches even though the exact combined string
    # is not itself in the set
    for prefix in GREETING_PREFIXES:
        if cleaned.startswith(prefix + " "):
            remainder = cleaned[len(prefix):].strip()
            if remainder in CASUAL_MESSAGES or remainder == "":
                return True

    return False