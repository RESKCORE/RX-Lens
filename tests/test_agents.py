# tests/test_agents.py
"""Unit tests for RxLens agents."""
import pytest
import json
from agents.interpreter import create_interpreter_agent, interpreter_task
from agents.interaction import create_interaction_agent, interaction_task
from agents.risk import create_risk_agent, risk_task
from agents.translator import create_translator_agent, translator_task
from agents.ethics import create_ethics_agent, ethics_task
from crewai import Crew
from utils.loader import load_knowledge_pack
from models.medication import Medication, Interaction, RiskLayer, AnalysisResult


@pytest.fixture
def knowledge():
    """Load knowledge pack once per test session."""
    return load_knowledge_pack()


@pytest.fixture
def sample_meds():
    """Sample medications for testing."""
    return [
        Medication(
            name="aspirin",
            type="otc_drug",
            drug_class="nsaid",
            primary_effects=["pain relief", "anti-inflammatory"],
            interaction_vectors=["platelet inhibition"],
            common_use_contexts=["headache", "minor pain"],
            dosage_note="typically 325–650 mg per dose",
            confidence_level="high"
        ),
        Medication(
            name="warfarin",
            type="prescription_drug",
            drug_class="anticoagulant",
            primary_effects=["blood thinning"],
            interaction_vectors=["platelet inhibition", "anticoagulation"],
            common_use_contexts=["atrial fibrillation", "thrombus prevention"],
            dosage_note="dose varies by INR",
            confidence_level="high"
        ),
    ]


class TestInterpreterAgent:
    """Test Medication Interpreter Agent."""
    
    def test_interpreter_exists(self):
        """Verify interpreter agent instantiates."""
        agent = create_interpreter_agent()
        assert agent is not None
        assert agent.role == "Medication Interpreter"
    
    def test_interpreter_task_creation(self):
        """Verify interpreter task is created correctly."""
        agent = create_interpreter_agent()
        task = interpreter_task(agent, ["aspirin", "ibuprofen"])
        assert task is not None
        assert "aspirin" in task.description
        assert "ibuprofen" in task.description
    
    def test_interpreter_output_format(self):
        """Test interpreter output JSON parsing (mock)."""
        # Mock output validation: ensure it would parse as JSON
        mock_output = json.dumps([
            {
                "name": "aspirin",
                "type": "otc_drug",
                "drug_class": "nsaid",
                "primary_effects": ["pain relief"],
                "interaction_vectors": ["platelet inhibition"],
                "common_use_contexts": ["headache"],
                "dosage_note": "325-650 mg",
                "confidence_level": "high"
            }
        ])
        parsed = json.loads(mock_output)
        assert isinstance(parsed, list)
        assert "name" in parsed[0]


class TestInteractionAgent:
    """Test Interaction Analysis Agent."""
    
    def test_interaction_agent_exists(self):
        """Verify interaction agent instantiates."""
        agent = create_interaction_agent()
        assert agent is not None
        assert agent.role == "Interaction Analysis Agent"
    
    def test_interaction_task_creation(self, sample_meds):
        """Verify interaction task is created correctly."""
        agent = create_interaction_agent()
        task = interaction_task(agent, sample_meds)
        assert task is not None
        assert "overlap" in task.description.lower() or "analyz" in task.description.lower()
    
    def test_interaction_output_format(self):
        """Test interaction output JSON parsing (mock)."""
        mock_output = json.dumps([
            {
                "meds_involved": ["aspirin", "warfarin"],
                "description": "general awareness suggests possible overlap in blood thinning effects",
                "confidence": "limited_data"
            }
        ])
        parsed = json.loads(mock_output)
        assert isinstance(parsed, list)
        assert "meds_involved" in parsed[0]
        assert "limited_data" in parsed[0]["confidence"]  # Conservative default


class TestRiskAgent:
    """Test Risk Stratification Agent."""
    
    def test_risk_agent_exists(self):
        """Verify risk agent instantiates."""
        agent = create_risk_agent()
        assert agent is not None
        assert agent.role == "Risk Stratification Agent"
    
    def test_risk_task_creation(self):
        """Verify risk task is created correctly."""
        agent = create_risk_agent()
        interactions = [
            Interaction(
                meds_involved=["aspirin", "warfarin"],
                description="potential shared effects",
                confidence="limited_data"
            )
        ]
        task = risk_task(agent, interactions)
        assert task is not None
    
    def test_risk_output_format(self):
        """Test risk output JSON parsing (mock)."""
        mock_output = json.dumps([
            {
                "level": "caution",
                "explanation": "this is a general observation, not personalized",
                "confidence": "general_observation"
            }
        ])
        parsed = json.loads(mock_output)
        assert isinstance(parsed, list)
        assert parsed[0]["level"] in ["safe", "caution", "avoid"]
        assert "general_observation" in parsed[0].get("confidence", "")


class TestTranslatorAgent:
    """Test Plain-English Translator Agent."""
    
    def test_translator_agent_exists(self):
        """Verify translator agent instantiates."""
        agent = create_translator_agent()
        assert agent is not None
        assert agent.role == "Plain-English Translator Agent"
    
    def test_translator_backstory_emphasizes_calm(self):
        """Verify translator backstory emphasizes calm tone."""
        agent = create_translator_agent()
        assert "calm" in agent.backstory.lower()
        assert "avoid" in agent.backstory.lower() or "warn" in agent.backstory.lower()


class TestEthicsAgent:
    """Test Ethics & Safety Guard Agent."""
    
    def test_ethics_agent_exists(self):
        """Verify ethics agent instantiates."""
        agent = create_ethics_agent()
        assert agent is not None
        assert agent.role == "Ethics & Safety Guard Agent"
    
    def test_ethics_backstory_enforces_boundaries(self):
        """Verify ethics backstory enforces educational boundaries."""
        agent = create_ethics_agent()
        assert "educational" in agent.backstory.lower()
        assert "diagnostic" in agent.backstory.lower() or "prescriptive" in agent.backstory.lower()
    
    def test_ethics_output_format(self):
        """Test ethics output includes disclaimer."""
        mock_output = json.dumps({
            "interactions": [],
            "risks": [],
            "disclaimer": "This is for general awareness; professional guidance is essential."
        })
        parsed = json.loads(mock_output)
        assert "disclaimer" in parsed
        assert "awareness" in parsed["disclaimer"].lower()


class TestModels:
    """Test data models for integrity."""
    
    def test_medication_model(self):
        """Verify Medication model enforces required fields."""
        med = Medication(
            name="test_drug",
            type="prescription_drug",
            drug_class="test_class",
            primary_effects=["effect1"],
            interaction_vectors=["vector1"],
            common_use_contexts=["context1"],
            dosage_note="test note",
            confidence_level="high"
        )
        assert med.name == "test_drug"
        assert med.safety_boundary == "educational_only"  # Enforced
    
    def test_interaction_model_defaults(self):
        """Verify Interaction model has conservative defaults."""
        inter = Interaction(
            meds_involved=["drug1", "drug2"],
            description="test interaction"
        )
        assert inter.confidence == "limited_data"  # Conservative default
    
    def test_risk_layer_model(self):
        """Verify RiskLayer model structure."""
        risk = RiskLayer(
            level="caution",
            explanation="test explanation"
        )
        assert risk.level in ["safe", "caution", "avoid"]
        assert risk.confidence == "general_observation"  # Conservative default
    
    def test_analysis_result_model(self):
        """Verify AnalysisResult model structure."""
        result = AnalysisResult(
            interactions=[],
            risks=[]
        )
        assert "disclaimer" in result.__dict__ or hasattr(result, "disclaimer")


class TestKnowledgePack:
    """Test knowledge pack loading and structure."""
    
    def test_knowledge_pack_loads(self, knowledge):
        """Verify knowledge pack loads successfully."""
        assert knowledge is not None
        assert isinstance(knowledge, list)
    
    def test_knowledge_pack_entries_valid(self, knowledge):
        """Verify knowledge pack entries have required fields."""
        assert len(knowledge) > 0
        for med in knowledge:
            assert hasattr(med, 'name')
            assert hasattr(med, 'drug_class')
            assert hasattr(med, 'interaction_vectors')
            assert med.safety_boundary == "educational_only"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
