# agents/translator.py
import os
from crewai import Agent, Task
from crewai.llm import LLM
from models.medication import AnalysisResult, Interaction, RiskLayer

_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    provider="groq",
    api_key=os.getenv("GROQ_API_KEY", "").strip(),
)

def create_translator_agent():
    return Agent(
        role="Plain-English Translator Agent",
        goal="Translate technical medical insights into clear, understandable language that helps people learn about their medications.",
        backstory="You explain medication interactions in simple, everyday language while preserving actual medication names and specific details. Instead of 'potential shared vector', say 'both medications work on the same body system'. For example: 'Aspirin and ibuprofen are both NSAIDs that can irritate the stomach lining' is better than 'substances may share mechanism'. Be specific, educational, and calm. Always use the actual medication names from the input.",
        verbose=False,
        allow_delegation=False,
        llm=_llm,
    )

def translator_task(agent: Agent, interactions: list[Interaction], risks: list[RiskLayer]) -> Task:
    return Task(
                description=f"""
Translate the following into clear, understandable language.

IMPORTANT:
- Keep EXACT medication names (never change to "substance1/substance2")
- Explain mechanisms simply (e.g., "Both thin the blood" vs "shared anticoagulant vector")
- Provide practical context (e.g., "which may increase bruising risk")
- Be specific but calm

Input:
Interactions: {interactions}
Risks: {risks}

Use ONLY the field names and structure below.
Do NOT add extra fields. Do NOT change field names.
Output **only** valid JSON — no extra text, no markdown.

Example of GOOD output:
"description": "Aspirin and ibuprofen are both NSAIDs that can irritate the stomach lining, potentially increasing the risk of stomach upset when taken together"

Example of BAD output:
"description": "Substances may have shared mechanism of action"

Exactly this structure:

{{
    "interactions": [
        {{
            "meds_involved": ["actual_med_name_1", "actual_med_name_2"],
            "description": "Clear explanation with specific mechanism",
            "confidence": "limited_data / medium / high"
        }}
    ],
    "risks": [
        {{
            "level": "safe / caution / avoid",
            "explanation": "Practical explanation of the risk",
            "confidence": "limited_data / medium / high"
        }}
    ],
    "disclaimer": "This is for general awareness only; professional guidance is essential."
}}

Return only the JSON object.
""",
                agent=agent,
                expected_output="AnalysisResult JSON with interactions, risks, disclaimer"
    )