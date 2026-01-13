# agents/ethics.py
import os
from crewai import Agent, Task
from crewai.llm import LLM
from models.medication import AnalysisResult

_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    provider="groq",
    api_key=os.getenv("GROQ_API_KEY", "").strip(),
)

def create_ethics_agent():
    return Agent(
        role="Ethics & Safety Guard Agent",
        goal="Ensure output is educational and non-prescriptive while preserving helpful details and actual medication names.",
        backstory="You review analysis for ethical framing. PRESERVE: actual medication names, specific mechanisms, helpful context (e.g., 'both medications affect the stomach'). REMOVE: commanding language ('you must', 'stop taking'). KEEP: awareness language ('may increase risk', 'could affect'). Your job is ethical framing while keeping the analysis useful and informative. Don't strip away all the helpful details.",
        verbose=False,
        allow_delegation=False,
        llm=_llm,
    )

def ethics_task(agent: Agent, result: AnalysisResult) -> Task:
    return Task(
                description=f"""
Review this analysis for ethical framing while preserving educational details.

IMPORTANT:
- KEEP actual medication names (e.g., "aspirin and ibuprofen")
- KEEP specific mechanisms (e.g., "both are NSAIDs")
- REMOVE commands ("you should", "must stop")
- KEEP awareness language ("may increase", "could affect")
- Ensure educational, not prescriptive tone

Input:
{result.model_dump_json()}

Use ONLY the field names and structure below.
Do NOT add extra fields. Do NOT change field names.
Output **only** valid JSON — no extra text, no markdown.

Exactly this structure:

{{
    "interactions": [
        {{
            "meds_involved": ["actual_medication_name_1", "actual_medication_name_2"],
            "description": "Preserve specific mechanism explanation from input",
            "confidence": "limited_data / medium / high"
        }}
    ],
    "risks": [
        {{
            "level": "safe / caution / avoid",
            "explanation": "Preserve helpful context while using awareness language",
            "confidence": "limited_data / medium / high"
        }}
    ],
    "disclaimer": "This is for general awareness only; professional guidance is essential."
}}

Return only the JSON object.
""",
                agent=agent,
                expected_output="Final AnalysisResult JSON with interactions, risks, disclaimer"
    )