# lib/data_manager.py
import sqlite3
import os

class DataManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS buildings (
                    building_uid TEXT PRIMARY KEY,
                    name TEXT,
                    address TEXT,
                    climate_zone TEXT,
                    building_type TEXT,
                    gfa_sqft REAL,
                    stories INTEGER,
                    year_built INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS simulation_runs (
                    run_id TEXT PRIMARY KEY,
                    building_uid TEXT REFERENCES buildings(building_uid),
                    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    error_log TEXT,
                    FOREIGN KEY (building_uid) REFERENCES buildings(building_uid)
                );

                CREATE TABLE IF NOT EXISTS scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    run_id TEXT REFERENCES simulation_runs(run_id),
                    scenario_type TEXT,
                    eui_total REAL,
                    eui_heating REAL,
                    eui_cooling REAL,
                    eui_lighting REAL,
                    eui_equipment REAL,
                    eui_fans REAL,
                    eui_pumps REAL,
                    emissions_tco2e REAL,
                    idf_path TEXT,
                    output_csv_path TEXT,
                    FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS building_models (
                    building_uid TEXT PRIMARY KEY,
                    run_id TEXT REFERENCES simulation_runs(run_id),
                    model_json TEXT,
                    source_summary TEXT,
                    FOREIGN KEY (building_uid) REFERENCES buildings(building_uid)
                );
            """)

    def get_table_names(self):
        """Get list of table names in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            return tables

    def save_building(self, building):
        """Save or update a building record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO buildings
                (building_uid, name, address, climate_zone, building_type, gfa_sqft, stories, year_built)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                building['building_uid'],
                building.get('name'),
                building.get('address'),
                building.get('climate_zone'),
                building.get('building_type'),
                building.get('gfa_sqft'),
                building.get('stories'),
                building.get('year_built')
            ))

    def get_building(self, building_uid):
        """Retrieve a building record by UID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM buildings WHERE building_uid = ?", (building_uid,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def save_simulation_run(self, run):
        """Save or update a simulation run record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO simulation_runs
                (run_id, building_uid, status, error_log)
                VALUES (?, ?, ?, ?)
            """, (
                run['run_id'],
                run['building_uid'],
                run.get('status', 'running'),
                run.get('error_log')
            ))

    def get_simulation_run(self, run_id):
        """Retrieve a simulation run by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM simulation_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def save_scenario(self, scenario):
        """Save or update a scenario result."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO scenarios
                (scenario_id, run_id, scenario_type, eui_total, eui_heating, eui_cooling,
                 eui_lighting, eui_equipment, eui_fans, eui_pumps, emissions_tco2e,
                 idf_path, output_csv_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scenario['scenario_id'],
                scenario['run_id'],
                scenario['scenario_type'],
                scenario.get('eui_total'),
                scenario.get('eui_heating'),
                scenario.get('eui_cooling'),
                scenario.get('eui_lighting'),
                scenario.get('eui_equipment'),
                scenario.get('eui_fans'),
                scenario.get('eui_pumps'),
                scenario.get('emissions_tco2e'),
                scenario.get('idf_path'),
                scenario.get('output_csv_path')
            ))

    def get_scenario(self, scenario_id):
        """Retrieve a scenario by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM scenarios WHERE scenario_id = ?", (scenario_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_scenarios_by_run(self, run_id):
        """Retrieve all scenarios for a simulation run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM scenarios WHERE run_id = ?", (run_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
