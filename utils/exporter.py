# utils/exporter.py - Export analysis results to various formats
import json
from datetime import datetime
from pathlib import Path

class AnalysisExporter:
    """Export analysis results to different formats."""
    
    @staticmethod
    def export_to_json(analysis: dict, medications: list, filepath: str = None):
        """Export analysis to JSON file."""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"rxlens_analysis_{timestamp}.json"
        
        export_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "medications_analyzed": medications,
                "tool": "RxLens v1.0"
            },
            "analysis": analysis
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    @staticmethod
    def export_to_text(analysis: dict, medications: list, filepath: str = None):
        """Export analysis to human-readable text file."""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"rxlens_analysis_{timestamp}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write("╔" + "═" * 88 + "╗\\n")
            f.write("║" + " " * 20 + "RxLens Medication Interaction Analysis Report" + " " * 23 + "║\\n")
            f.write("╚" + "═" * 88 + "╝\\n\\n")
            
            # Metadata
            f.write("┌─ Analysis Information " + "─" * 64 + "┐\\n")
            f.write(f"│  📅 Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}" + " " * 36 + "│\\n")
            f.write(f"│  💊 Medications: {', '.join(medications)}" + " " * (66 - len(', '.join(medications))) + "│\\n")
            f.write("└" + "─" * 88 + "┘\\n\\n")
            
            # Summary
            interactions = analysis.get('interactions', [])
            risks = analysis.get('risks', [])
            risk_level = risks[0].get('level', 'safe').upper() if risks else 'SAFE'
            
            f.write("┌─ Quick Summary " + "─" * 71 + "┐\\n")
            f.write(f"│  🔍 Interactions Found: {len(interactions)}" + " " * 55 + "│\\n")
            f.write(f"│  ⚠️  Risk Level: {risk_level}" + " " * (65 - len(risk_level)) + "│\\n")
            f.write("└" + "─" * 88 + "┘\\n\\n")
            
            # Interactions
            f.write("╔" + "═" * 88 + "╗\\n")
            f.write("║  🔬 DETECTED INTERACTIONS" + " " * 62 + "║\\n")
            f.write("╚" + "═" * 88 + "╝\\n\\n")
            
            if interactions:
                for i, inter in enumerate(interactions, 1):
                    f.write(f"┌─ Interaction #{i} " + "─" * 69 + "┐\\n")
                    f.write(f"│  Medications: {', '.join(inter.get('meds_involved', []))}" + " " * (70 - len(', '.join(inter.get('meds_involved', [])))) + "│\\n")
                    f.write("├" + "─" * 88 + "┤\\n")
                    
                    # Wrap description
                    desc = inter.get('description', 'N/A')
                    import textwrap
                    wrapped_desc = textwrap.wrap(desc, width=84)
                    for line in wrapped_desc:
                        f.write(f"│  {line}" + " " * (86 - len(line)) + "│\\n")
                    
                    f.write("├" + "─" * 88 + "┤\\n")
                    f.write(f"│  Confidence: {inter.get('confidence', 'N/A').upper()}" + " " * (74 - len(inter.get('confidence', 'N/A'))) + "│\\n")
                    f.write("└" + "─" * 88 + "┘\\n\\n")
            else:
                f.write("   ✓ No significant interactions detected.\\n\\n")
            
            # Risks
            f.write("╔" + "═" * 88 + "╗\\n")
            f.write("║  ⚠️  RISK ASSESSMENT" + " " * 67 + "║\\n")
            f.write("╚" + "═" * 88 + "╝\\n\\n")
            
            if risks:
                for idx, risk in enumerate(risks, 1):
                    level = risk.get('level', 'N/A').upper()
                    icon = "🛑" if level == "AVOID" else "⚠️" if level == "CAUTION" else "✅"
                    
                    f.write("┌─ Risk Assessment " + "─" * 70 + "┐\\n")
                    f.write(f"│  {icon} Level: {level}" + " " * (82 - len(level)) + "│\\n")
                    f.write("├" + "─" * 88 + "┤\\n")
                    
                    # Wrap explanation
                    expl = risk.get('explanation', 'N/A')
                    import textwrap
                    wrapped_expl = textwrap.wrap(expl, width=84)
                    for line in wrapped_expl:
                        f.write(f"│  {line}" + " " * (86 - len(line)) + "│\\n")
                    
                    f.write("├" + "─" * 88 + "┤\\n")
                    f.write(f"│  Confidence: {risk.get('confidence', 'N/A').upper()}" + " " * (74 - len(risk.get('confidence', 'N/A'))) + "│\\n")
                    f.write("└" + "─" * 88 + "┘\\n\\n")
            else:
                f.write("   ✓ No specific risk factors identified.\\n\\n")
            
            # Disclaimer
            f.write("╔" + "═" * 88 + "╗\\n")
            f.write("║  📋 IMPORTANT DISCLAIMER" + " " * 63 + "║\\n")
            f.write("╠" + "═" * 88 + "╣\\n")
            
            disclaimer = analysis.get('disclaimer', 'This is for educational purposes only.')
            import textwrap
            wrapped_disclaimer = textwrap.wrap(disclaimer, width=84)
            for line in wrapped_disclaimer:
                f.write(f"║  {line}" + " " * (86 - len(line)) + "║\\n")
            
            f.write("╚" + "═" * 88 + "╝\\n\\n")
            
            # Footer
            f.write("Generated by RxLens - Medication Awareness Tool\\n")
            f.write("For educational purposes only. Consult healthcare professionals.\\n")
        
        return filepath
    
    @staticmethod
    def export_to_markdown(analysis: dict, medications: list, filepath: str = None):
        """Export analysis to Markdown file."""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"rxlens_analysis_{timestamp}.md"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# RxLens Medication Interaction Analysis\\n\\n")
            
            f.write(f"**Analysis Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  \\n")
            f.write(f"**Medications:** {', '.join(medications)}\\n\\n")
            
            f.write("---\\n\\n")
            
            # Interactions
            f.write("## 🔍 Detected Interactions\\n\\n")
            interactions = analysis.get('interactions', [])
            if interactions:
                for i, inter in enumerate(interactions, 1):
                    meds = ', '.join(inter.get('meds_involved', []))
                    desc = inter.get('description', 'N/A')
                    conf = inter.get('confidence', 'N/A')
                    f.write(f"### {i}. {meds}\\n\\n")
                    f.write(f"**Description:** {desc}\\n\\n")
                    f.write(f"**Confidence:** `{conf}`\\n\\n")
            else:
                f.write("✅ No significant interactions detected.\\n\\n")
            
            # Risks
            f.write("## ⚠️ Risk Assessment\\n\\n")
            risks = analysis.get('risks', [])
            if risks:
                for risk in risks:
                    level = risk.get('level', 'N/A').upper()
                    icon = "🛑" if level == "AVOID" else "⚠️" if level == "CAUTION" else "✅"
                    f.write(f"### {icon} {level}\\n\\n")
                    f.write(f"{risk.get('explanation', 'N/A')}\\n\\n")
                    f.write(f"**Confidence:** `{risk.get('confidence', 'N/A')}`\\n\\n")
            else:
                f.write("No specific risk factors identified.\\n\\n")
            
            # Disclaimer
            f.write("---\\n\\n")
            f.write("## 📋 Disclaimer\\n\\n")
            f.write(f"> {analysis.get('disclaimer', 'This is for educational purposes only.')}\\n")
        
        return filepath
