# agents/consensus.py - Multi-agent consensus voting system
from crewai import Agent, Task, Crew
from agents.risk import create_risk_agent, risk_task
from models.medication import RiskLayer
import os

# Groq LLM configuration
_llm = f"groq/{os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}"

def create_consensus_risk_agents():
    """Create 3 independent risk assessment agents for consensus."""
    agents = []
    
    for i in range(1, 4):
        agent = Agent(
            role=f"Risk Assessment Specialist #{i}",
            goal=f"Provide independent risk assessment with confidence scoring",
            backstory=f"""You are risk assessor #{i} in a panel of experts.
            Your role is to independently evaluate medication combinations and provide
            your own assessment without being influenced by others.
            Focus on: {'pharmacokinetic interactions' if i == 1 else 'pharmacodynamic effects' if i == 2 else 'clinical significance'}.
            Be transparent about uncertainty.""",
            verbose=False,
            llm=_llm,
        )
        agents.append(agent)
    
    return agents

def run_consensus_risk_assessment(interactions: list, med_names: list):
    """Run 3 agents in parallel and aggregate their risk assessments."""
    agents = create_consensus_risk_agents()
    tasks = []
    
    # Create tasks for each agent
    for i, agent in enumerate(agents, 1):
        task = Task(
            description=f"""
Assess the risk level for these medication interactions.

Medications: {', '.join(med_names)}
Detected Interactions: {interactions}

Focus area: {'Metabolic pathways and drug metabolism' if i == 1 else 'Direct drug-drug effects and mechanism overlap' if i == 2 else 'Clinical relevance and real-world significance'}

Provide your independent assessment in JSON format:

{{
    "risks": [
        {{
            "level": "safe / caution / avoid",
            "explanation": "Your reasoning for this assessment",
            "confidence": "limited_data / medium / high"
        }}
    ]
}}

Be honest about confidence. Return only valid JSON.
""",
            agent=agent,
            expected_output="Risk assessment JSON"
        )
        tasks.append(task)
    
    # Run agents
    crew = Crew(agents=agents, tasks=tasks, verbose=0)
    results = crew.kickoff()
    
    return results

def aggregate_consensus(agent_results: list):
    """Aggregate multiple agent assessments into consensus."""
    import json
    
    # Parse results
    all_assessments = []
    for result in agent_results:
        try:
            raw = getattr(result, "raw", str(result)).strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                if len(parts) >= 3:
                    body = parts[2] if parts[1].strip().lower().startswith("json") else parts[1]
                    raw = body.strip()
            data = json.loads(raw)
            all_assessments.append(data)
        except:
            continue
    
    if not all_assessments:
        return None
    
    # Aggregate risk levels (majority vote)
    risk_votes = {"safe": 0, "caution": 0, "avoid": 0}
    explanations = []
    confidences = []
    
    for assessment in all_assessments:
        risks = assessment.get('risks', [])
        if risks:
            risk = risks[0]
            level = risk.get('level', 'caution')
            risk_votes[level] += 1
            explanations.append(risk.get('explanation', ''))
            confidences.append(risk.get('confidence', 'limited_data'))
    
    # Determine consensus level
    consensus_level = max(risk_votes, key=risk_votes.get)
    
    # Calculate consensus confidence
    conf_scores = {"high": 3, "medium": 2, "limited_data": 1}
    avg_conf_score = sum(conf_scores.get(c, 1) for c in confidences) / len(confidences)
    
    if avg_conf_score >= 2.5:
        consensus_confidence = "high"
    elif avg_conf_score >= 1.5:
        consensus_confidence = "medium"
    else:
        consensus_confidence = "limited_data"
    
    # Combine explanations
    combined_explanation = f"Consensus from {len(all_assessments)} independent assessments: "
    combined_explanation += " Multiple experts noted: ".join(set(explanations[:2]))  # Avoid duplication
    
    return {
        "risks": [{
            "level": consensus_level,
            "explanation": combined_explanation,
            "confidence": consensus_confidence,
            "voting_breakdown": risk_votes,
            "agent_count": len(all_assessments)
        }]
    }
