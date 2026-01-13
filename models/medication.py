# models/medication.py
from typing import List, Optional
from pydantic import BaseModel

class Medication(BaseModel):
    name: str
    type: str  # e.g., "prescription_drug", "otc_drug", "supplement"
    drug_class: str
    primary_effects: List[str]
    interaction_vectors: List[str]
    common_use_contexts: List[str]
    dosage_note: str
    confidence_level: str  # e.g., "high", "medium", "low"
    safety_boundary: str = "educational_only"  # Fixed per PRD

class Interaction(BaseModel):
    meds_involved: List[str]
    description: str  # Abstract, e.g., "Potential additive hypotension"
    confidence: str = "limited_data"  # Default conservative

class RiskLayer(BaseModel):
    level: str  # "safe", "caution", "avoid"
    explanation: str
    confidence: str = "general_observation"

class AnalysisResult(BaseModel):
    interactions: List[Interaction]
    risks: List[RiskLayer]
    disclaimer: str = "This is for awareness only; consult a professional."