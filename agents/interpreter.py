# agents/interpreter.py
import os
from crewai import Agent, Task
from crewai.llm import LLM
from models.medication import Medication
from utils.loader import load_knowledge_pack

_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    provider="groq",
    api_key=os.getenv("GROQ_API_KEY", "").strip(),
)

knowledge = load_knowledge_pack()  # Load once, offline

def create_interpreter_agent():
    return Agent(
        role="Medication Interpreter",
        goal="Abstractly identify and classify user-input substances from static knowledge, flagging unknowns with high caution and defaulting to low confidence.",
        backstory="You focus on high-level categorization using only provided knowledge. Never imply completeness—always note 'limited data' for partial matches or unknowns. Avoid any phrasing that suggests medical certainty, like 'this is'—use 'this appears to match' instead.",
        verbose=False,
        allow_delegation=False,
        llm=_llm,
    )

def interpreter_task(agent: Agent, user_inputs: list[str]) -> Task:
    return Task(
                description=f"""
Interpret these substances: {', '.join(user_inputs)}.

Map each to the closest matching entry in the static knowledge pack.
Use ONLY the field names and structure shown below.
Do NOT add extra fields. Do NOT change field names.
If no good match, use 'limited data' in confidence_level and fill other fields with empty lists or 'unknown'.

Output **only** valid JSON — no extra text, no markdown, no explanations.

Exactly this structure:

[
    {{
        "name": "exact name",
        "type": "prescription_drug / otc_drug / supplement",
        "drug_class": "high-level class",
        "primary_effects": ["effect1", "effect2"],
        "interaction_vectors": ["vector1", "vector2"],
        "common_use_contexts": ["context1"],
        "dosage_note": "non-actionable note",
        "confidence_level": "high / medium / low",
        "safety_boundary": "educational_only"
    }}
]

Return only the JSON array.
""",
        agent=agent,
        expected_output="List[Medication] in JSON format"
    )