# agents/risk.py
import os
from crewai import Agent, Task
from crewai.llm import LLM
from models.medication import Interaction, RiskLayer

_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    provider="groq",
    api_key=os.getenv("GROQ_API_KEY", "").strip(),
)

def create_risk_agent():
    return Agent(
        role="Risk Stratification Agent",
        goal="Assign general, non-personalized risk layers (safe/caution/avoid) with heavy conservative bias and explicit uncertainty.",
        backstory="Layers are high-level observations only (e.g., 'caution' for most overlaps). Always include phrases like 'this is a general observation, not personalized'. Rarely use 'avoid'—prefer 'caution'. No probabilities or severity; focus on awareness.",
        verbose=False,
        allow_delegation=False,
        llm=_llm,
    )

def risk_task(agent: Agent, interactions: list[Interaction]) -> Task:
    return Task(
                description="""
Stratify risks from the provided interactions. Bias toward 'caution'.

Use ONLY the field names and structure below.
Do NOT add extra fields. Do NOT change field names.
Output **only** valid JSON — no extra text, no markdown.

Exactly this structure:

{
    "risks": [
        {
            "level": "safe / caution / avoid",
            "explanation": "brief educational observation of why this level was chosen",
            "confidence": "limited_data / medium / high"
        }
    ]
}

Return only the JSON object.
""",
                agent=agent,
                expected_output="A JSON object with 'risks' key"
    )