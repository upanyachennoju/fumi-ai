SUMMARIZATION_PROMPT = """You are Fumi's Conversation Summarizer.
Analyze the following conversation between the user and Fumi.
Write a concise, single-sentence summary of the conversation.
Do not include any introductions, meta-commentary, or markdown wrappers. Output only the plain summary sentence.

Conversation:
{conversation}
"""

EXTRACTION_PROMPT = """You are Fumi's Memory Extractor.
Analyze the conversation between the user and the assistant.
Extract structured long-term memory points that are important for Fumi to remember about the user.

You MUST respond with a single JSON object. Do NOT wrap your response in markdown code blocks or write any explanations.
The JSON object must have exactly the following structure:
{
  "preferences": ["user's preferences/tastes"],
  "goals": ["user's goals/aspirations"],
  "projects": ["user's projects"],
  "people": ["important people mentioned"],
  "habits": ["user's habits/routines"],
  "memories": ["general factual memories"],
  "ignore": false
}

If the conversation contains no long-term memories or important personal facts to store, set "ignore" to true and leave all list fields empty:
{
  "preferences": [],
  "goals": [],
  "projects": [],
  "people": [],
  "habits": [],
  "memories": [],
  "ignore": true
}

Conversation to analyze:
{conversation}
"""
