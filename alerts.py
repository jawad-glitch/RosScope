#!/usr/bin/env python3
import uuid
import threading
import sqlite3
import os
from datetime import datetime
from notifier import notification_manager


class AlertManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rosscope_alerts.db")
        self._alerts = {}
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    z_score REAL NOT NULL,
                    state TEXT NOT NULL,
                    fired_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    resolved_at TEXT,
                    note TEXT
                )
            """)
            conn.commit()

            cursor = conn.execute(
                "SELECT id, topic, z_score, state, fired_at, acknowledged_at, resolved_at, note FROM alerts"
            )
            for row in cursor.fetchall():
                alert = {
                    'id': row[0],
                    'topic': row[1],
                    'z_score': row[2],
                    'state': row[3],
                    'fired_at': row[4],
                    'acknowledged_at': row[5],
                    'resolved_at': row[6],
                    'note': row[7]
                }
                self._alerts[alert['id']] = alert

    def _save_alert(self, alert):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO alerts
                   (id, topic, z_score, state, fired_at, acknowledged_at, resolved_at, note)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (alert['id'], alert['topic'], alert['z_score'], alert['state'],
                 alert['fired_at'], alert['acknowledged_at'], alert['resolved_at'], alert['note'])
            )
            conn.commit()

    def fire(self, topic, z_score):
        with self._lock:
            for alert in self._alerts.values():
                if alert['topic'] == topic and alert['state'] in ('firing', 'acknowledged'):
                    return alert['id']

            alert_id = str(uuid.uuid4())
            alert = {
                'id': alert_id,
                'topic': topic,
                'z_score': round(z_score, 3),
                'state': 'firing',
                'fired_at': datetime.utcnow().isoformat(),
                'acknowledged_at': None,
                'resolved_at': None,
                'note': None
            }
            self._alerts[alert_id] = alert
            self._save_alert(alert)

        notification_manager.notify(alert)
        return alert_id

    def acknowledge(self, alert_id):
        """Transition firing → acknowledged."""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                return False
            if alert['state'] != 'firing':
                return False
            alert['state'] = 'acknowledged'
            alert['acknowledged_at'] = datetime.utcnow().isoformat()
            self._save_alert(alert)
        return True

    def resolve(self, alert_id, note=None):
        """Transition acknowledged/firing → resolved."""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                return False
            if alert['state'] == 'resolved':
                return False
            alert['state'] = 'resolved'
            alert['resolved_at'] = datetime.utcnow().isoformat()
            alert['note'] = note
            self._save_alert(alert)
        return True

    def get_active(self):
        """Return all firing and acknowledged alerts."""
        with self._lock:
            return [
                a for a in self._alerts.values()
                if a['state'] in ('firing', 'acknowledged')
            ]

    def get_all(self):
        """Return all alerts including resolved."""
        with self._lock:
            return list(self._alerts.values())

    def get_by_id(self, alert_id):
        """Return a single alert by id."""
        with self._lock:
            return self._alerts.get(alert_id)


alert_manager = AlertManager()