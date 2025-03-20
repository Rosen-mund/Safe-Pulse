import sqlite3
import os
import json
from datetime import datetime
from math import radians, cos
import threading

class Database:
    def __init__(self, db_path="women_safety.db"):
        """Initialize the database by creating tables using a temporary connection."""
        self.db_path = db_path
        # Thread-local storage for per-thread connections
        self.thread_local = threading.local()
        # Use a one-off connection to create tables, ensuring it is used in a single thread.
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            self.create_tables(cursor)
            conn.commit()

    def connect(self):
        """Connect to the SQLite database in a thread-safe manner.
        Each thread gets its own connection.
        """
        if not hasattr(self.thread_local, 'conn') or self.thread_local.conn is None:
            # Each thread creates its own connection
            self.thread_local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.thread_local.conn.row_factory = sqlite3.Row
            self.thread_local.cursor = self.thread_local.conn.cursor()
        return self.thread_local.conn, self.thread_local.cursor

    def close(self):
        """Close the database connection for the current thread."""
        if hasattr(self.thread_local, 'conn') and self.thread_local.conn:
            self.thread_local.conn.close()
            self.thread_local.conn = None
            self.thread_local.cursor = None

    def create_tables(self, cursor):
        """Create necessary tables if they don't exist."""
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        # Emergency contacts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            phone TEXT,
            relationship TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Reports table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            reporter_id TEXT,
            description TEXT,
            anonymized_description TEXT,
            latitude REAL,
            longitude REAL,
            severity TEXT,
            categories TEXT,
            status TEXT,
            verification_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (reporter_id) REFERENCES users (id)
        )
        ''')

        # Journeys table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS journeys (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            start_latitude REAL,
            start_longitude REAL,
            destination_latitude REAL,
            destination_longitude REAL,
            travel_mode TEXT,
            status TEXT,
            route_safety TEXT,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Alerts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            reporter_id TEXT,
            alert_type TEXT,
            description TEXT,
            latitude REAL,
            longitude REAL,
            severity TEXT,
            status TEXT,
            verification_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (reporter_id) REFERENCES users (id)
        )
        ''')

        # SOS history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sos_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            latitude REAL,
            longitude REAL,
            message TEXT,
            contacts_notified TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

    # User methods
    def create_user(self, user_id, name=None, email=None):
        """Create a new user."""
        conn, cursor = self.connect()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email, now, now)
        )
        conn.commit()
        return user_id

    def get_user(self, user_id):
        """Get user by ID."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = dict(cursor.fetchone() or {})
        return result

    # Emergency contact methods
    def add_emergency_contact(self, user_id, name, phone, relationship=None):
        """Add an emergency contact for a user."""
        conn, cursor = self.connect()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO emergency_contacts (user_id, name, phone, relationship, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, phone, relationship, now)
        )
        conn.commit()
        return cursor.lastrowid

    def get_emergency_contacts(self, user_id):
        """Get all emergency contacts for a user."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM emergency_contacts WHERE user_id = ?", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_emergency_contact(self, contact_id, user_id):
        """Delete an emergency contact."""
        conn, cursor = self.connect()
        cursor.execute(
            "DELETE FROM emergency_contacts WHERE id = ? AND user_id = ?",
            (contact_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

    # Report methods
    def create_report(self, report_id, reporter_id, description, anonymized_description, 
                      latitude, longitude, severity, categories, status="submitted"):
        """Create a new incident report."""
        conn, cursor = self.connect()
        now = datetime.now().isoformat()
        categories_json = json.dumps(categories)
        cursor.execute(
            """INSERT INTO reports 
               (id, reporter_id, description, anonymized_description, latitude, longitude, 
                severity, categories, status, verification_count, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (report_id, reporter_id, description, anonymized_description, latitude, longitude, 
             severity, categories_json, status, 0, now, now)
        )
        conn.commit()
        return report_id

    def get_report(self, report_id):
        """Get report by ID."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['categories'] = json.loads(result['categories'])
            return result
        return None

    def get_reports_by_area(self, latitude, longitude, radius_km=5.0):
        """Get reports within a radius of a location."""
        conn, cursor = self.connect()
        lat_range = radius_km / 111.0
        lng_range = radius_km / (111.0 * cos(radians(latitude)))
        cursor.execute(
            """SELECT * FROM reports 
               WHERE latitude BETWEEN ? AND ?
               AND longitude BETWEEN ? AND ?""",
            (latitude - lat_range, latitude + lat_range, 
             longitude - lng_range, longitude + lng_range)
        )
        reports = []
        for row in cursor.fetchall():
            report = dict(row)
            report['categories'] = json.loads(report['categories'])
            distance = self.calculate_distance(
                latitude, longitude, report['latitude'], report['longitude']
            )
            if distance <= radius_km:
                report['distance_km'] = round(distance, 2)
                reports.append(report)
        return reports

    def verify_report(self, report_id, verification_type="confirm"):
        """Verify or dispute a report."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        report = dict(cursor.fetchone() or {})
        if not report:
            return False
        if verification_type == "confirm":
            new_count = report.get('verification_count', 0) + 1
            cursor.execute(
                "UPDATE reports SET verification_count = ?, updated_at = ? WHERE id = ?",
                (new_count, datetime.now().isoformat(), report_id)
            )
            if new_count >= 3:
                cursor.execute(
                    "UPDATE reports SET status = ?, updated_at = ? WHERE id = ?",
                    ("verified", datetime.now().isoformat(), report_id)
                )
        else:
            cursor.execute(
                "UPDATE reports SET status = ?, updated_at = ? WHERE id = ?",
                ("disputed", datetime.now().isoformat(), report_id)
            )
        conn.commit()
        return True

    # Journey methods
    def create_journey(self, journey_id, user_id, start_latitude, start_longitude,
                       destination_latitude, destination_longitude, travel_mode, route_safety):
        """Create a new journey."""
        conn, cursor = self.connect()
        now = datetime.now().isoformat()
        route_safety_json = json.dumps(route_safety)
        cursor.execute(
            """INSERT INTO journeys 
               (id, user_id, start_latitude, start_longitude, destination_latitude, 
                destination_longitude, travel_mode, status, route_safety, start_time) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (journey_id, user_id, start_latitude, start_longitude, destination_latitude, 
             destination_longitude, travel_mode, "active", route_safety_json, now)
        )
        conn.commit()
        return journey_id

    def update_journey_status(self, journey_id, status, end_time=None):
        """Update journey status."""
        conn, cursor = self.connect()
        if end_time is None and status == "completed":
            end_time = datetime.now().isoformat()
        if end_time:
            cursor.execute(
                "UPDATE journeys SET status = ?, end_time = ? WHERE id = ?",
                (status, end_time, journey_id)
            )
        else:
            cursor.execute(
                "UPDATE journeys SET status = ? WHERE id = ?",
                (status, journey_id)
            )
        conn.commit()
        return cursor.rowcount > 0

    def get_journey(self, journey_id):
        """Get journey by ID."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM journeys WHERE id = ?", (journey_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['route_safety'] = json.loads(result['route_safety'])
            return result
        return None

    # Alert methods
    def create_alert(self, alert_id, reporter_id, alert_type, description, 
                     latitude, longitude, severity, status="active"):
        """Create a new emergency alert."""
        conn, cursor = self.connect()
        now = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO alerts 
               (id, reporter_id, alert_type, description, latitude, longitude, 
                severity, status, verification_count, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (alert_id, reporter_id, alert_type, description, latitude, longitude, 
             severity, status, 1, now, now)  # Start with verification count 1 (self-verified)
        )
        conn.commit()
        return alert_id

    def get_alert(self, alert_id):
        """Get alert by ID."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        return dict(cursor.fetchone() or {})

    def get_active_alerts(self, latitude, longitude, radius_km=5.0):
        """Get active alerts within a radius of a location."""
        conn, cursor = self.connect()
        lat_range = radius_km / 111.0
        lng_range = radius_km / (111.0 * cos(radians(latitude)))
        cursor.execute(
            """SELECT * FROM alerts 
               WHERE status = 'active'
               AND latitude BETWEEN ? AND ?
               AND longitude BETWEEN ? AND ?""",
            (latitude - lat_range, latitude + lat_range, 
             longitude - lng_range, longitude + lng_range)
        )
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            distance = self.calculate_distance(
                latitude, longitude, alert['latitude'], alert['longitude']
            )
            if distance <= radius_km:
                alert['distance_km'] = round(distance, 2)
                alerts.append(alert)
        alerts.sort(key=lambda x: (
            0 if x["severity"] == "high" else (1 if x["severity"] == "medium" else 2),
            x["distance_km"]
        ))
        return alerts

    def verify_alert(self, alert_id, verification_type="confirm"):
        """Verify or dispute an alert."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        alert = dict(cursor.fetchone() or {})
        if not alert:
            return False
        if verification_type == "confirm":
            new_count = alert.get('verification_count', 0) + 1
            cursor.execute(
                "UPDATE alerts SET verification_count = ?, updated_at = ? WHERE id = ?",
                (new_count, datetime.now().isoformat(), alert_id)
            )
            if new_count >= 3 and alert.get('severity') != "high":
                cursor.execute(
                    "UPDATE alerts SET severity = ?, updated_at = ? WHERE id = ?",
                    ("high", datetime.now().isoformat(), alert_id)
                )
        else:
            cursor.execute(
                "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
                ("disputed", datetime.now().isoformat(), alert_id)
            )
        conn.commit()
        return True

    def resolve_alert(self, alert_id, resolution_details=None):
        """Mark an alert as resolved."""
        conn, cursor = self.connect()
        now = datetime.now().isoformat()
        if resolution_details:
            resolution_json = json.dumps(resolution_details)
            cursor.execute(
                "UPDATE alerts SET status = ?, updated_at = ?, resolution_details = ? WHERE id = ?",
                ("resolved", now, resolution_json, alert_id)
            )
        else:
            cursor.execute(
                "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
                ("resolved", now, alert_id)
            )
        conn.commit()
        return cursor.rowcount > 0

    # SOS methods
    def create_sos(self, user_id, latitude, longitude, message, contacts_notified):
        """Record an SOS event."""
        conn, cursor = self.connect()
        now = datetime.now().isoformat()
        contacts_json = json.dumps(contacts_notified)
        cursor.execute(
            """INSERT INTO sos_history 
               (user_id, latitude, longitude, message, contacts_notified, created_at) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, latitude, longitude, message, contacts_json, now)
        )
        conn.commit()
        return cursor.lastrowid

    def get_sos_history(self, user_id):
        """Get SOS history for a user."""
        conn, cursor = self.connect()
        cursor.execute("SELECT * FROM sos_history WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        sos_events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['contacts_notified'] = json.loads(event['contacts_notified'])
            sos_events.append(event)
        return sos_events

    # Helper methods
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km using the Haversine formula."""
        from math import radians, cos, sin, asin, sqrt
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
