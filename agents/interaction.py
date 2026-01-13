# agents/interaction.py
import os
from crewai import Agent, Task
from crewai.llm import LLM
from models.medication import Interaction, Medication

_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    provider="groq",
    api_key=os.getenv("GROQ_API_KEY", "").strip(),
)

def create_interaction_agent():
    return Agent(
        role="Interaction Analysis Agent",
        goal="Identify specific interaction mechanisms between medications using their actual names, explaining how they might interact in plain, educational language.",
        backstory="You analyze how different medications might interact based on their mechanisms. Always use the ACTUAL medication names provided (e.g., 'aspirin and ibuprofen', never 'substance1 and substance2'). Explain the specific mechanism in simple terms (e.g., 'both medications reduce blood clotting', 'both can irritate the stomach lining'). Be specific but educational, avoiding alarm. Focus on the biological mechanism that creates the interaction.",
        verbose=False,
        allow_delegation=False,
        llm=_llm,
    )

def interaction_task(agent: Agent, meds: list[Medication]) -> Task:
    med_names = [m.name for m in meds]
    return Task(
                description=f"""
Analyze potential interactions for: {med_names}.

IMPORTANT: Use the ACTUAL medication names in your response: {', '.join(med_names)}
NEVER use generic terms like "substance1" or "substance2".

For each pair, explain:
1. The specific mechanism (e.g., "Both are NSAIDs that inhibit COX enzymes")
2. What this means practically (e.g., "which can increase stomach irritation")
3. Use simple, educational language

Use ONLY the field names and structure below.
Do NOT add extra fields. Do NOT change field names.
Output **only** valid JSON — no extra text, no markdown.

Exactly this structure:

{{
    "interactions": [
        {{
            "meds_involved": ["{med_names[0] if len(med_names) > 0 else 'med1'}", "{med_names[1] if len(med_names) > 1 else 'med2'}"],
            "description": "Specific mechanism in plain language (e.g., 'Both medications reduce blood clotting, which combined can increase bleeding risk')",
            "confidence": "limited_data / medium / high"
        }}
    ]
}}

Return only the JSON object.
""",
                agent=agent,
                expected_output="A JSON object with 'interactions' key containing actual medication names"
    )