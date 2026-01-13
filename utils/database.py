# utils/database.py - Session persistence with SQLite
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class AnalysisDatabase:
    """Manages analysis history storage."""
    
    def __init__(self, db_path="rxlens_history.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create database schema if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                medications TEXT NOT NULL,
                interactions_count INTEGER,
                risk_level TEXT,
                full_result TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, medications: list, result: dict):
        """Save an analysis to history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        meds_str = ", ".join(medications)
        interactions_count = len(result.get('interactions', []))
        
        # Determine highest risk level
        risks = result.get('risks', [])
        risk_level = "safe"
        if risks:
            risk_priorities = {"avoid": 3, "caution": 2, "safe": 1}
            highest = max(risks, key=lambda r: risk_priorities.get(r.get('level', 'safe'), 0))
            risk_level = highest.get('level', 'safe')
        
        cursor.execute("""
            INSERT INTO analyses (timestamp, medications, interactions_count, risk_level, full_result)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, meds_str, interactions_count, risk_level, json.dumps(result)))
        
        conn.commit()
        conn.close()
    
    def get_recent_analyses(self, limit=10):
        """Retrieve recent analysis history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, medications, interactions_count, risk_level
            FROM analyses
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_analysis_by_id(self, analysis_id: int):
        """Retrieve full analysis by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT full_result FROM analyses WHERE id = ?
        """, (analysis_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def clear_history(self):
        """Clear all analysis history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses")
        conn.commit()
        conn.close()
