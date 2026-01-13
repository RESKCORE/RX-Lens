# app.py - Simple CLI Interface for RxLens
import json
import os
import sys
import logging
import textwrap
import time
from datetime import datetime
from colorama import Fore, Style, Back, init
from dotenv import load_dotenv
from crewai import Crew
from agents.interpreter import create_interpreter_agent, interpreter_task
from agents.interaction import create_interaction_agent, interaction_task
from agents.risk import create_risk_agent, risk_task
from agents.translator import create_translator_agent, translator_task
from agents.ethics import create_ethics_agent, ethics_task
from agents.consensus import run_consensus_risk_assessment, aggregate_consensus
from models.medication import Medication, AnalysisResult, Interaction
from utils.database import AnalysisDatabase
from utils.exporter import AnalysisExporter

# Load environment variables from .env (for GROQ_API_KEY)
load_dotenv()

# Suppress noisy logs from providers
logging.getLogger("litellm").setLevel(logging.ERROR)
logging.getLogger("crewai").setLevel(logging.ERROR)
os.environ["OPENAI_API_VERBOSE"] = "0"

init(autoreset=True)  # Auto-reset colors after each print

# Risk level color indicators (semantic, calm)
RISK_COLORS = {
    "safe": Fore.GREEN + "✓ SAFE" + Style.RESET_ALL,
    "caution": Fore.YELLOW + "⚠️ CAUTION" + Style.RESET_ALL,
    "avoid": Fore.RED + "⛔ AVOID" + Style.RESET_ALL
}

# Confidence level colors
CONFIDENCE_COLORS = {
    "high": Fore.GREEN,
    "medium": Fore.YELLOW,
    "limited_data": Style.DIM + Fore.WHITE
}

# Box drawing characters for professional borders
BOX = {
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
    "h": "═", "v": "║", "t": "╦", "b": "╩",
    "l": "╠", "r": "╣", "c": "╬"
}
# Initialize database and exporter
db = AnalysisDatabase()
exporter = AnalysisExporter()

def clear_screen():
    """Clear terminal for a clean view."""
    print("\033[H\033[J", end="")


def _extract_json(output, label):
    """Extract JSON-able string from CrewOutput (handles ```json fences)."""
    raw = getattr(output, "raw", str(output)).strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        # Prefer body after the first fence; handle optional 'json' tag
        if len(parts) >= 3:
            body = parts[2] if parts[1].strip().lower().startswith("json") else parts[1]
            raw = body.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"{label} JSON parse failed: {e}. Raw output: {raw}")

def print_header():
    """Print application header with professional styling."""
    clear_screen()
    width = 120
    print(BOX["tl"] + BOX["h"] * (width - 2) + BOX["tr"])
    title = "RxLens: Medication Awareness Tool"
    subtitle = "Offline • Educational • Non-Prescriptive"
    print(BOX["v"] + f"{Style.BRIGHT}{title:^{width-2}}{Style.RESET_ALL}" + BOX["v"])
    print(BOX["v"] + f"{Fore.CYAN}{subtitle:^{width-2}}{Style.RESET_ALL}" + BOX["v"])
    print(BOX["bl"] + BOX["h"] * (width - 2) + BOX["br"])
    print()

def show_menu():
    """Display main menu options."""
    print(f"{Style.BRIGHT}┌─ Main Menu ─────────────────────────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}│{Style.RESET_ALL}  {Fore.CYAN}[1]{Style.RESET_ALL} 🔬 {Style.BRIGHT}Analyze{Style.RESET_ALL}  - Run new medication analysis          {Style.BRIGHT}│{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}│{Style.RESET_ALL}  {Fore.CYAN}[2]{Style.RESET_ALL} 📜 {Style.BRIGHT}History{Style.RESET_ALL}  - View recent analyses                 {Style.BRIGHT}│{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}│{Style.RESET_ALL}  {Fore.CYAN}[3]{Style.RESET_ALL} 💾 {Style.BRIGHT}Export{Style.RESET_ALL}   - Export last analysis (json/txt/md)   {Style.BRIGHT}│{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}│{Style.RESET_ALL}  {Fore.CYAN}[4]{Style.RESET_ALL} ❓ {Style.BRIGHT}Help{Style.RESET_ALL}     - Show this menu                      {Style.BRIGHT}│{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}│{Style.RESET_ALL}  {Fore.CYAN}[5]{Style.RESET_ALL} 🚪 {Style.BRIGHT}Quit{Style.RESET_ALL}     - Exit application                     {Style.BRIGHT}│{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}└─────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
    print(f"{Style.DIM}💡 Tip: Type medication names directly or use menu numbers{Style.RESET_ALL}")
    print()

def show_history():
    """Display recent analysis history."""
    history = db.get_recent_analyses(10)
    
    if not history:
        print(f"{Style.DIM}No analysis history found.{Style.RESET_ALL}\n")
        return
    
    print(f"{Style.BRIGHT}📜 Recent Analyses{Style.RESET_ALL}")
    print("─" * 120)
    
    for record in history:
        analysis_id, timestamp, medications, interactions, risk = record
        dt = datetime.fromisoformat(timestamp)
        formatted_time = dt.strftime("%b %d, %I:%M %p")
        
        risk_icon = RISK_COLORS.get(risk, risk.upper())
        interaction_text = f"{interactions} interaction(s)" if interactions else "No interactions"
        
        print(f"  {Style.DIM}[{analysis_id}]{Style.RESET_ALL} {formatted_time} - {Fore.CYAN}{medications}{Style.RESET_ALL}")
        print(f"      {interaction_text} • Risk: {risk_icon}")
        print()

def export_last_analysis(format_type='json'):
    """Export the most recent analysis."""
    history = db.get_recent_analyses(1)
    
    if not history:
        print(f"{Fore.RED}✗ No analysis found to export.{Style.RESET_ALL}\n")
        return
    
    analysis_id = history[0][0]
    medications = history[0][2].split(", ")
    result = db.get_analysis_by_id(analysis_id)
    
    if not result:
        print(f"{Fore.RED}✗ Failed to load analysis.{Style.RESET_ALL}\n")
        return
    
    try:
        if format_type == 'json':
            filepath = exporter.export_to_json(result, medications)
        elif format_type == 'txt':
            filepath = exporter.export_to_text(result, medications)
        elif format_type == 'md':
            filepath = exporter.export_to_markdown(result, medications)
        else:
            print(f"{Fore.RED}✗ Invalid format. Use: json, txt, or md{Style.RESET_ALL}\n")
            return
        
        print(f"{Fore.GREEN}✓ Exported to: {filepath}{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Export failed: {str(e)}{Style.RESET_ALL}\n")

def get_user_input():
    """Get medication input from user."""
    print(f"{Style.DIM}Enter medications (comma-separated):{Style.RESET_ALL}")
    print(f"{Style.DIM}Example: aspirin, ibuprofen, vitamin-d{Style.RESET_ALL}")
    print(f"{Style.DIM}Add 'consensus' for multi-agent voting: aspirin, warfarin consensus{Style.RESET_ALL}")
    user_input = input("> ").strip().lower()
    return user_input

def run_analysis(user_inputs, use_consensus=False):
    """Run the 5-agent workflow with optional consensus mode."""
    # Check for consensus flag
    if 'consensus' in user_inputs:
        use_consensus = True
        user_inputs = user_inputs.replace('consensus', '').strip()
    
    meds = [m.strip() for m in user_inputs.split(',') if m.strip()]
    
    if not meds:
        print(f"{Fore.RED}✗ Please enter at least one substance.{Style.RESET_ALL}\n")
        return None
    
    print(f"\n{Fore.CYAN}► Analyzing:{Style.RESET_ALL} {', '.join(meds)}")
    
    if use_consensus:
        print(f"{Style.BRIGHT}{Fore.YELLOW}🗳️  CONSENSUS MODE: Running 3 independent risk assessors{Style.RESET_ALL}")
    
    print(f"{Style.DIM}Processing through {'7-agent' if use_consensus else '5-agent'} workflow...{Style.RESET_ALL}\n")
    
    # Progress bar
    stages = [
        "Interpreting substances",
        "Analyzing interactions",
        "Running consensus vote" if use_consensus else "Assessing risks",
        "Aggregating assessments" if use_consensus else "Translating results",
        "Translating results" if use_consensus else "Applying safety checks",
        "Applying safety checks" if use_consensus else None
    ]
    stages = [s for s in stages if s]  # Remove None
    
    def show_progress(stage_num):
        bar_width = 40
        total_stages = len(stages)
        filled = int(bar_width * stage_num / total_stages)
        bar = "█" * filled + "░" * (bar_width - filled)
        percent = int(100 * stage_num / total_stages)
        print(f"\r{Fore.CYAN}[{bar}] {percent}%{Style.RESET_ALL} {stages[stage_num-1] if stage_num > 0 else ''}", end="", flush=True)
    
    show_progress(0)
    
    try:
        # Step 1: Interpreter
        show_progress(1)
        interpreter = create_interpreter_agent()
        interp_task = interpreter_task(interpreter, meds)
        interp_output = Crew(agents=[interpreter], tasks=[interp_task], verbose=0).kickoff()
        meds_list = _extract_json(interp_output, "Interpreter")
        if not isinstance(meds_list, list):
            meds_list = [meds_list]
        
        # Step 2: Interaction Analysis
        show_progress(2)
        if len(meds_list) < 2:
            interactions = []
        else:
            interaction_a = create_interaction_agent()
            inter_task = interaction_task(interaction_a, [Medication(**m) for m in meds_list])
            inter_output = Crew(agents=[interaction_a], tasks=[inter_task], verbose=0).kickoff()
            interactions = _extract_json(inter_output, "Interaction")
            if isinstance(interactions, dict):
                interactions = interactions.get("interactions", [])
            if not isinstance(interactions, list):
                interactions = [interactions]
        
        # Step 3: Risk Assessment (normal or consensus)
        show_progress(3)
        if use_consensus and interactions:
            # Consensus mode: 3 agents vote
            med_names = [m.get('name', 'Unknown') if isinstance(m, dict) else str(m) for m in meds_list]
            agent_results = run_consensus_risk_assessment(interactions, med_names)
            
            show_progress(4)
            consensus_result = aggregate_consensus(agent_results)
            risks = consensus_result.get('risks', []) if consensus_result else []
        else:
            # Normal mode: single risk agent
            risk_a = create_risk_agent()
            risk_t = risk_task(risk_a, interactions)
            risk_output = Crew(agents=[risk_a], tasks=[risk_t], verbose=0).kickoff()
            risks = _extract_json(risk_output, "Risk")
            if isinstance(risks, dict):
                risks = risks.get("risks", [])
            if not isinstance(risks, list):
                risks = [risks]
        
        # Step 4: Translation
        show_progress(5 if use_consensus else 4)
        trans_a = create_translator_agent()
        trans_t = translator_task(trans_a, interactions, risks)
        trans_output = Crew(agents=[trans_a], tasks=[trans_t], verbose=0).kickoff()
        trans_result = _extract_json(trans_output, "Translator")
        
        # Step 5: Ethics
        show_progress(6 if use_consensus else 5)
        ethics_a = create_ethics_agent()
        ethics_t = ethics_task(ethics_a, AnalysisResult(**trans_result))
        final_output = Crew(agents=[ethics_a], tasks=[ethics_t], verbose=0).kickoff()
        final_analysis = _extract_json(final_output, "Ethics")
        
        if isinstance(final_analysis, list):
            final_analysis = {
                "medications": meds_list,
                "interactions": interactions,
                "risks": risks,
                "analysis": final_analysis,
            }

        # Normalize fields
        final_analysis.setdefault(
            "medications",
            [m.get("name", "Unknown") if isinstance(m, dict) else str(m) for m in meds_list],
        )
        final_analysis.setdefault("interactions", interactions if interactions else [])
        final_analysis.setdefault("risks", risks if risks else [])
        
        if 'disclaimer' not in final_analysis:
            final_analysis['disclaimer'] = "This is for general awareness only; professional guidance is essential."
        
        print(f"\r{Fore.GREEN}[{'█' * 40}] 100%{Style.RESET_ALL} Complete!" + " " * 30)
        print()
        
        # Save to database
        db.save_analysis(meds, final_analysis)
        
        return final_analysis
    
    except Exception as e:
        print(f"{Fore.RED}Workflow error: {str(e)}{Style.RESET_ALL}\n")
        return None

def wrap_text(text, width):
    """Wrap text to fit within specified width."""
    return textwrap.fill(text, width=width, break_long_words=False, break_on_hyphens=False)

def visible_len(text):
    """Get visible length of string (excluding ANSI codes)."""
    import re
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return len(ansi_escape.sub('', text))

def colorize_confidence(conf):
    """Apply color to confidence level."""
    color = CONFIDENCE_COLORS.get(conf, Style.RESET_ALL)
    return f"{color}{conf}{Style.RESET_ALL}"

def print_table_row(columns, widths, border_left="║", border_right="║", sep="│"):
    """Print a formatted table row with proper alignment."""
    parts = []
    for col, width in zip(columns, widths):
        visible = visible_len(col)
        padding = width - visible
        if padding < 0:
            padding = 0
        parts.append(f" {col}{' ' * padding} ")
    print(f"{border_left}{sep.join(parts)}{border_right}")

def display_results(analysis):
    """Structured output with professional ASCII tables and calm semantics."""
    width = 120
    print(BOX["tl"] + BOX["h"] * (width - 2) + BOX["tr"])
    title = f"{Style.BRIGHT}ANALYSIS RESULTS{Style.RESET_ALL}"
    print(BOX["v"] + f"{title:^{width+8}}" + BOX["v"])
    print(BOX["bl"] + BOX["h"] * (width - 2) + BOX["br"])
    print()

    # Timestamp
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    print(f"{Style.DIM}Analysis performed on {timestamp}{Style.RESET_ALL}")
    print()

    # Quick Summary Stats
    interactions = analysis.get('interactions', [])
    risks = analysis.get('risks', [])
    
    # Determine highest risk level
    risk_level = "SAFE"
    if risks:
        risk_priorities = {"avoid": 3, "caution": 2, "safe": 1}
        highest = max(risks, key=lambda r: risk_priorities.get(r.get('level', 'safe'), 0))
        risk_level = highest.get('level', 'safe').upper()
    
    summary_parts = []
    summary_parts.append(f"{Fore.CYAN}{len(interactions)}{Style.RESET_ALL} interaction(s)")
    summary_parts.append(f"Risk: {RISK_COLORS.get(risk_level.lower(), risk_level)}")
    
    print(f"{Style.BRIGHT}📊 Summary:{Style.RESET_ALL} {' • '.join(summary_parts)}")
    print()
    print("─" * 120)
    print()

    # Medications Section
    print(f"{Style.BRIGHT}► Medications Analyzed{Style.RESET_ALL}")
    print("─" * 120)
    meds = analysis.get('medications', [])
    if meds:
        for i, med in enumerate(meds, 1):
            name = med if isinstance(med, str) else med.get('name', 'Unknown')
            print(f"  {Fore.CYAN}{i}.{Style.RESET_ALL} {name.capitalize()}")
    else:
        print(f"  {Style.DIM}No medications identified{Style.RESET_ALL}")
    print()
    print()

    # Key Findings Section
    if interactions or risks:
        print(f"{Style.BRIGHT}💡 Key Findings{Style.RESET_ALL}")
        print("─" * 120)
        
        # Add interaction highlights
        if interactions:
            for inter in interactions:
                meds_list = ', '.join(inter.get('meds_involved', []))
                desc = inter.get('description', 'Interaction noted')
                # Extract key phrase (first sentence or first 80 chars)
                key_phrase = desc.split('.')[0] if '.' in desc else desc[:80]
                print(f"  • {Fore.YELLOW}Interaction:{Style.RESET_ALL} {meds_list} - {key_phrase}")
        
        # Add risk highlights
        if risks:
            for risk in risks:
                level = risk.get('level', 'caution')
                expl = risk.get('explanation', '')
                key_phrase = expl.split('.')[0] if '.' in expl else expl[:80]
                icon = "⛔" if level == "avoid" else "⚠️" if level == "caution" else "✓"
                print(f"  • {icon} {Fore.CYAN}Risk:{Style.RESET_ALL} {key_phrase}")
        
        print()
        print()

    # Interactions Section
    print(f"{Style.BRIGHT}► Detected Interactions{Style.RESET_ALL}")
    print("─" * 120)
    interactions = analysis.get('interactions', [])
    if interactions:
        # Table header - widths: [3, 30, 65, 12] with 2 padding each + 3 separators = 120
        col_widths = [3, 30, 65, 12]
        total_width = sum(col_widths) + 8 + 3  # 8 for padding (2 per column), 3 for separators
        print(BOX["tl"] + BOX["h"] * (col_widths[0] + 2) + BOX["t"] + BOX["h"] * (col_widths[1] + 2) + BOX["t"] + BOX["h"] * (col_widths[2] + 2) + BOX["t"] + BOX["h"] * (col_widths[3] + 2) + BOX["tr"])
        print_table_row(["#", "Substances", "Description", "Confidence"], col_widths)
        print(BOX["l"] + BOX["h"] * (col_widths[0] + 2) + BOX["c"] + BOX["h"] * (col_widths[1] + 2) + BOX["c"] + BOX["h"] * (col_widths[2] + 2) + BOX["c"] + BOX["h"] * (col_widths[3] + 2) + BOX["r"])
        
        for i, inter in enumerate(interactions, 1):
            meds_inv = ', '.join(inter.get('meds_involved', ['Unknown']))
            # Highlight if generic names are used (agent error)
            if 'substance' in meds_inv.lower():
                meds_inv = f"{Style.DIM}[names not preserved]{Style.RESET_ALL}"
            desc = inter.get('description', 'General observation')
            conf = inter.get('confidence', 'limited_data')
            conf_colored = colorize_confidence(conf)
            
            # Truncate meds_inv to fit (handle ANSI codes)
            if visible_len(meds_inv) > col_widths[1]:
                # Find position to truncate considering visible chars only
                truncated = ""
                for char in meds_inv:
                    if visible_len(truncated + char + "...") <= col_widths[1]:
                        truncated += char
                    else:
                        break
                meds_display = truncated + "..."
            else:
                meds_display = meds_inv
            
            # Wrap description if too long
            if len(desc) > col_widths[2]:
                wrapped_desc = textwrap.wrap(desc, width=col_widths[2], break_long_words=False)
                print_table_row([str(i), meds_display, wrapped_desc[0], conf_colored], col_widths)
                for line in wrapped_desc[1:]:
                    print_table_row(["", "", line, ""], col_widths)
            else:
                print_table_row([str(i), meds_display, desc, conf_colored], col_widths)
        
        print(BOX["bl"] + BOX["h"] * (col_widths[0] + 2) + BOX["b"] + BOX["h"] * (col_widths[1] + 2) + BOX["b"] + BOX["h"] * (col_widths[2] + 2) + BOX["b"] + BOX["h"] * (col_widths[3] + 2) + BOX["br"])
    else:
        print(f"  {Fore.GREEN}✓ No multi-substance overlaps noted{Style.RESET_ALL} {Style.DIM}(general awareness applies){Style.RESET_ALL}")
    print()
    print()

    # Risk Assessment Section
    print(f"{Style.BRIGHT}► Risk Assessment{Style.RESET_ALL}")
    
    # Show consensus info if present
    if risks and risks[0].get('voting_breakdown'):
        voting = risks[0]['voting_breakdown']
        agent_count = risks[0].get('agent_count', 3)
        print(f"{Style.DIM}  🗳️  Consensus from {agent_count} independent assessors: " +
              f"Safe({voting.get('safe', 0)}) • Caution({voting.get('caution', 0)}) • Avoid({voting.get('avoid', 0)}){Style.RESET_ALL}")
    
    print("─" * 120)
    risks = analysis.get('risks', [])
    if risks:
        # Table header - widths: [16, 80, 14] with padding + separators = 120
        risk_widths = [16, 80, 14]
        print(BOX["tl"] + BOX["h"] * (risk_widths[0] + 2) + BOX["t"] + BOX["h"] * (risk_widths[1] + 2) + BOX["t"] + BOX["h"] * (risk_widths[2] + 2) + BOX["tr"])
        print_table_row(["Level", "Explanation", "Confidence"], risk_widths)
        print(BOX["l"] + BOX["h"] * (risk_widths[0] + 2) + BOX["c"] + BOX["h"] * (risk_widths[1] + 2) + BOX["c"] + BOX["h"] * (risk_widths[2] + 2) + BOX["r"])
        
        for risk in risks:
            level = risk.get('level', 'caution')
            color_level = RISK_COLORS.get(level, "⚠️ CAUTION")
            expl = risk.get('explanation', 'General observation')
            conf = risk.get('confidence', 'limited_data')
            conf_colored = colorize_confidence(conf)
            
            # Wrap explanation if too long
            if len(expl) > risk_widths[1]:
                wrapped_expl = textwrap.wrap(expl, width=risk_widths[1], break_long_words=False)
                print_table_row([color_level, wrapped_expl[0], conf_colored], risk_widths)
                for line in wrapped_expl[1:]:
                    print_table_row(["", line, ""], risk_widths)
            else:
                print_table_row([color_level, expl, conf_colored], risk_widths)
        
        print(BOX["bl"] + BOX["h"] * (risk_widths[0] + 2) + BOX["b"] + BOX["h"] * (risk_widths[1] + 2) + BOX["b"] + BOX["h"] * (risk_widths[2] + 2) + BOX["br"])
    else:
        print(f"  {RISK_COLORS['caution']} General observation: Proceed with awareness. {Style.DIM}(limited_data){Style.RESET_ALL}")
    print()
    print()

    # Educational Note Section
    print(BOX["tl"] + BOX["h"] * 118 + BOX["tr"])
    print(BOX["v"] + f" {Style.BRIGHT}📋 Educational Note{Style.RESET_ALL}" + " " * 99 + BOX["v"])
    print(BOX["l"] + BOX["h"] * 118 + BOX["r"])
    print(BOX["v"] + " " * 120 + BOX["v"])  # Empty line for padding
    
    disclaimer = analysis.get('disclaimer', 'This is for general awareness only; professional guidance is essential.')
    wrapped_lines = textwrap.wrap(disclaimer, width=112)
    
    for line in wrapped_lines:
        print(BOX["v"] + f"   {Style.DIM}{line:<112}{Style.RESET_ALL}   " + BOX["v"])
    
    print(BOX["v"] + " " * 120 + BOX["v"])  # Empty line for padding
    print(BOX["bl"] + BOX["h"] * 118 + BOX["br"])
    print()
    print()

def main():
    """Main CLI loop with menu system."""
    print_header()
    show_menu()
    
    last_analysis = None
    
    while True:
        user_input = input(f"{Fore.CYAN}rxlens>{Style.RESET_ALL} ").strip()
        user_input_lower = user_input.lower()
        
        # Handle numeric menu options
        if user_input == '1':
            user_input_lower = 'analyze'
        elif user_input == '2':
            user_input_lower = 'history'
        elif user_input == '3':
            user_input_lower = 'export'
        elif user_input == '4':
            user_input_lower = 'help'
        elif user_input == '5':
            user_input_lower = 'quit'
        
        if user_input_lower in ['quit', 'exit', 'q', '5']:
            clear_screen()
            print(f"{Fore.GREEN}Thank you for using RxLens. Stay informed, stay safe.{Style.RESET_ALL}\n")
            sys.exit(0)
        
        elif user_input_lower == 'help':
            show_menu()
        
        elif user_input_lower == 'history':
            show_history()
        
        elif user_input_lower.startswith('export'):
            # Parse export format: "export json" or just "export"
            parts = user_input_lower.split()
            format_type = parts[1] if len(parts) > 1 else 'json'
            export_last_analysis(format_type)
        
        elif user_input_lower in ['analyze', 'analyse', '']:
            # Start analysis workflow with input prompt
            meds_input = get_user_input()
            
            if meds_input.lower() in ['quit', 'exit', 'q']:
                continue
            
            analysis = run_analysis(meds_input)
            
            if analysis:
                last_analysis = analysis
                display_results(analysis)
        
        else:
            # Treat any other input as direct medication entry
            analysis = run_analysis(user_input)
            
            if analysis:
                last_analysis = analysis
                display_results(analysis)

if __name__ == "__main__":
    main()
