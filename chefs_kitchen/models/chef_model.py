from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from chefs_kitchen.utils.sql_utils import get_db_connection
from chefs_kitchen.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

@dataclass
class Chef:
    id: int
    name: str
    specialty: str
    years_experience: int
    signature_dishes: int
    age: int
    wins: int = 0
    cookoffs: int = 0

def create_chef(name: str, specialty: str, years_experience: int, signature_dishes: int, age: int) -> None:
    if not (18 <= age <= 65):
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 65.")
    if years_experience < 0:
        raise ValueError(f"Invalid years_experience: {years_experience}. Must be non-negative.")
    if signature_dishes < 0:
        raise ValueError(f"Invalid signature_dishes: {signature_dishes}. Must be non-negative.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM chefs WHERE name = ?", (name,))
            if cursor.fetchone():
                raise ValueError(f"Chef with name '{name}' already exists")

            cursor.execute("""
                INSERT INTO chefs (name, specialty, years_experience, signature_dishes, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, specialty, years_experience, signature_dishes, age))
            conn.commit()
            logger.info(f"Chef {name} created successfully.")

    except sqlite3.IntegrityError:
        raise ValueError(f"Chef with name '{name}' already exists")
    except sqlite3.Error as e:
        raise e

def get_chef_by_id(chef_id: int) -> Chef:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, specialty, years_experience, signature_dishes, age, wins, cookoffs
                FROM chefs WHERE id = ?
            """, (chef_id,))
            row = cursor.fetchone()
            if row:
                return Chef(*row)
            else:
                raise ValueError(f"Chef with ID {chef_id} not found.")
    except sqlite3.Error as e:
        raise e

def get_chef_by_name(chef_name: str) -> Chef:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, specialty, years_experience, signature_dishes, age, wins, cookoffs
                FROM chefs WHERE name = ?
            """, (chef_name,))
            row = cursor.fetchone()
            if row:
                return Chef(*row)
            else:
                raise ValueError(f"Chef '{chef_name}' not found.")
    except sqlite3.Error as e:
        raise e

def delete_chef(chef_id: int) -> None:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM chefs WHERE id = ?", (chef_id,))
            if cursor.fetchone() is None:
                raise ValueError(f"Chef with ID {chef_id} not found.")

            cursor.execute("DELETE FROM chefs WHERE id = ?", (chef_id,))
            conn.commit()
            logger.info(f"Chef {chef_id} deleted successfully.")

    except sqlite3.Error as e:
        raise e

def update_chef_stats(chef_id: int, result: str) -> None:
    if result not in {'win', 'loss'}:
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM chefs WHERE id = ?", (chef_id,))
            if cursor.fetchone() is None:
                raise ValueError(f"Chef with ID {chef_id} not found.")

            if result == 'win':
                cursor.execute("UPDATE chefs SET cookoffs = cookoffs + 1, wins = wins + 1 WHERE id = ?", (chef_id,))
            else:
                cursor.execute("UPDATE chefs SET cookoffs = cookoffs + 1 WHERE id = ?", (chef_id,))
            conn.commit()
            logger.info(f"Updated stats for chef {chef_id} with result {result}.")

    except sqlite3.Error as e:
        raise e

def initialize_schema():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chefs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    specialty TEXT,
                    years_experience INTEGER,
                    signature_dishes INTEGER,
                    age INTEGER,
                    wins INTEGER DEFAULT 0,
                    cookoffs INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            logger.info("Chef table initialized successfully.")
    except sqlite3.Error as e:
        raise e
