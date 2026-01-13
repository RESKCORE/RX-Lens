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
from models.medication import Medication, AnalysisResult, Interaction

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

def get_user_input():
    """Get medication input from user."""
    print(f"{Style.DIM}Enter medications (comma-separated):{Style.RESET_ALL}")
    print(f"{Style.DIM}Example: aspirin, ibuprofen, vitamin-d{Style.RESET_ALL}")
    user_input = input("> ").strip().lower()
    return user_input

def run_analysis(user_inputs):
    """Run the 5-agent workflow."""
    meds = [m.strip() for m in user_inputs.split(',') if m.strip()]
    
    if not meds:
        print(f"{Fore.RED}✗ Please enter at least one substance.{Style.RESET_ALL}\n")
        return None
    
    print(f"\n{Fore.CYAN}► Analyzing:{Style.RESET_ALL} {', '.join(meds)}")
    print(f"{Style.DIM}Processing through 5-agent workflow...{Style.RESET_ALL}\n")
    
    # Progress bar
    stages = [
        "Interpreting substances",
        "Analyzing interactions",
        "Assessing risks",
        "Translating results",
        "Applying safety checks"
    ]
    
    def show_progress(stage_num):
        bar_width = 40
        filled = int(bar_width * stage_num / 5)
        bar = "█" * filled + "░" * (bar_width - filled)
        percent = int(100 * stage_num / 5)
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
        
        # Step 2: Interaction Analysis (skip hallucinations for single med)
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
        
        # Step 3: Risk Stratification
        show_progress(3)
        risk_a = create_risk_agent()
        risk_t = risk_task(risk_a, interactions)
        risk_output = Crew(agents=[risk_a], tasks=[risk_t], verbose=0).kickoff()
        risks = _extract_json(risk_output, "Risk")
        if isinstance(risks, dict):
            risks = risks.get("risks", [])
        if not isinstance(risks, list):
            risks = [risks]
        
        # Step 4: Plain-English Translation
        show_progress(4)
        trans_a = create_translator_agent()
        trans_t = translator_task(trans_a, interactions, risks)
        trans_output = Crew(agents=[trans_a], tasks=[trans_t], verbose=0).kickoff()
        trans_result = _extract_json(trans_output, "Translator")
        
        # Step 5: Ethics Guard
        show_progress(5)
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

        # Ensure required fields are present and normalized
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
    """Main CLI loop."""
    print_header()
    
    while True:
        user_input = get_user_input()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            clear_screen()
            print("Thank you for using RxLens.\n")
            sys.exit(0)
        
        analysis = run_analysis(user_input)
        
        if analysis:
            display_results(analysis)
        
        print(f"{Style.DIM}Enter 'q' to quit, or enter new medications to analyze.{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()
