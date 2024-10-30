import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('scraping_analyzer.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Create preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                context TEXT NOT NULL,
                preference_value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create analysis_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                result JSON NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create expert_feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expert_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                feedback JSON NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def save_preference(self, agent_type, context, value):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO preferences (agent_type, context, preference_value)
            VALUES (?, ?, ?)
        ''', (agent_type, context, value))
        self.conn.commit()

    def get_preference(self, agent_type, context):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT preference_value 
            FROM preferences 
            WHERE agent_type = ? AND context = ?
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (agent_type, context))
        result = cursor.fetchone()
        return result[0] if result else 1.0

    def save_analysis(self, url, result):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_history (url, result)
            VALUES (?, ?)
        ''', (url, json.dumps(result)))
        self.conn.commit()

    def save_feedback(self, url, feedback):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO expert_feedback (url, feedback)
            VALUES (?, ?)
        ''', (url, json.dumps(feedback)))
        self.conn.commit()

    def get_recent_analyses(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT url, result, timestamp
            FROM analysis_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()