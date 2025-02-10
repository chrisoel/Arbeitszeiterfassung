#!/usr/bin/env python
"""
database_manager.py
-------------------
Datenbankmanager für die Zeiterfassung.

Dieses Modul verwaltet die SQLite-Datenbank und stellt Methoden zum Speichern und Abrufen von Zeiteinträgen
und Redmine-Ticketdaten bereit.

Version: CHOE 10.02.2025
"""

import sqlite3
import logging
from typing import List, Tuple, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Datenbankmanager für die Zeiterfassung.

    Diese Klasse kapselt alle Operationen, die den Zugriff und die Verwaltung der SQLite-Datenbank
    betreffen. Sie ermöglicht die Initialisierung der benötigten Tabellen, das Speichern und Abrufen
    von Zeiteinträgen sowie das Verwalten von Redmine-Tickets.
    """
    
    DB_FILE: str = "zeiterfassung.db"

    def __init__(self) -> None:
        """
        Initialisiert den DatabaseManager und stellt eine Verbindung zur SQLite-Datenbank her.
        Falls die Datenbank noch nicht existiert, wird sie erstellt und initialisiert.
        """
        self.conn = sqlite3.connect(self.DB_FILE)
        self.cursor = self.conn.cursor()
        self.initialize_db()

    def initialize_db(self) -> None:
        """
        Initialisiert die Datenbanktabellen, falls diese noch nicht existieren.
        """
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    project TEXT,
                    work_package TEXT,
                    duration REAL,
                    UNIQUE(date, project, work_package, duration)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS redmine_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER UNIQUE,
                    subject TEXT,
                    project TEXT,
                    status TEXT,
                    estimated_hours REAL,
                    updated_on TEXT,
                    user TEXT
                )
            ''')
            self.conn.commit()
            logger.debug("Datenbank initialisiert.")
        except Exception as error:
            logger.error("Fehler bei der Datenbankinitialisierung: %s", error)

    def record_time_entry(self, date_str: str, project: str, work_package: str, duration: float) -> None:
        """
        Speichert einen Zeiteintrag in die Tabelle work_log.

        Args:
            date_str (str): Datum des Eintrags im Format YYYY-MM-DD.
            project (str): Name des Projekts.
            work_package (str): Bezeichnung des Arbeitspakets.
            duration (float): Dauer des Eintrags in Stunden.
        """
        try:
            self.cursor.execute(
                "INSERT INTO work_log (date, project, work_package, duration) VALUES (?, ?, ?, ?)",
                (date_str, project, work_package, duration)
            )
            self.conn.commit()
            logger.info("Zeiteintrag gespeichert: %s, %s, %s, %s", date_str, project, work_package, duration)
        except Exception as error:
            logger.error("Fehler beim Speichern des Zeiteintrags: %s", error)
            raise

    def fetch_avg_duration_per_work_package(self) -> List[Tuple[Any, Any]]:
        """
        Gibt den durchschnittlichen Zeitaufwand pro Arbeitspaket zurück.

        Returns:
            List[Tuple[Any, Any]]: Eine Liste von Tupeln, wobei jedes Tupel das Arbeitspaket und
            dessen durchschnittliche Dauer enthält.
        """
        try:
            self.cursor.execute(
                "SELECT work_package, AVG(duration) as avg_duration FROM work_log GROUP BY work_package"
            )
            return self.cursor.fetchall()
        except Exception as error:
            logger.error("Fehler beim Abrufen der Durchschnittsdauer: %s", error)
            return []

    def fetch_all_entries(self) -> List[Tuple]:
        """
        Ruft alle Zeiteinträge aus der Tabelle work_log ab.

        Returns:
            List[Tuple]: Eine Liste von Tupeln mit den Feldern (date, project, work_package, duration).
        """
        try:
            self.cursor.execute("SELECT date, project, work_package, duration FROM work_log")
            return self.cursor.fetchall()
        except Exception as error:
            logger.error("Fehler beim Abrufen der Einträge: %s", error)
            return []

    def fetch_entries_for_day(self, day: str) -> List[Tuple]:
        """
        Ruft alle Zeiteinträge für einen bestimmten Tag ab.

        Args:
            day (str): Der Tag im Format YYYY-MM-DD.

        Returns:
            List[Tuple]: Eine Liste von Tupeln mit den Feldern (date, project, work_package, duration) für den angegebenen Tag.
        """
        try:
            pattern = day + "%"
            self.cursor.execute("SELECT date, project, work_package, duration FROM work_log WHERE date LIKE ?", (pattern,))
            return self.cursor.fetchall()
        except Exception as error:
            logger.error("Fehler beim Abrufen der Einträge für den Tag %s: %s", day, error)
            return []

    def fetch_avg_duration_for(self, project: str, work_package: str) -> float:
        """
        Berechnet die durchschnittliche Dauer für ein bestimmtes Projekt und Arbeitspaket.

        Args:
            project (str): Der Name des Projekts.
            work_package (str): Das Arbeitspaket.

        Returns:
            float: Die durchschnittliche Dauer oder 0, falls kein Eintrag vorhanden ist.
        """
        try:
            self.cursor.execute(
                "SELECT AVG(duration) FROM work_log WHERE project=? AND work_package=?",
                (project, work_package)
            )
            result = self.cursor.fetchone()[0]
            return result if result is not None else 0
        except Exception as error:
            logger.error("Fehler beim Abrufen des Durchschnitts für %s / %s: %s", project, work_package, error)
            return 0

    def ticket_exists(self, ticket_id: int) -> bool:
        """
        Überprüft, ob ein Ticket mit der angegebenen ID in der Tabelle redmine_tickets existiert.

        Args:
            ticket_id (int): Die ID des Tickets.

        Returns:
            bool: True, wenn das Ticket existiert, andernfalls False.
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM redmine_tickets WHERE ticket_id = ?", (ticket_id,))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as error:
            logger.error("Fehler bei der Überprüfung des Tickets %s: %s", ticket_id, error)
            return False

    def insert_ticket(self, ticket_data: dict) -> None:
        """
        Fügt ein neues Ticket in die Tabelle redmine_tickets ein.

        Args:
            ticket_data (dict): Ein Dictionary mit den Ticketdaten.
        """
        try:
            self.cursor.execute('''
                INSERT INTO redmine_tickets (ticket_id, subject, project, status, estimated_hours, updated_on, user)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticket_data.get("ticket_id"),
                ticket_data.get("subject"),
                ticket_data.get("project"),
                ticket_data.get("status"),
                ticket_data.get("estimated_hours"),
                ticket_data.get("updated_on"),
                ticket_data.get("user")
            ))
            self.conn.commit()
            logger.info("Ticket %s in die Datenbank eingefügt.", ticket_data.get("ticket_id"))
        except Exception as error:
            logger.error("Fehler beim Einfügen des Tickets %s: %s", ticket_data.get("ticket_id"), error)

    def update_ticket(self, ticket_data: dict) -> None:
        """
        Aktualisiert ein vorhandenes Ticket in der Tabelle redmine_tickets.

        Args:
            ticket_data (dict): Ein Dictionary mit den aktualisierten Ticketdaten.
        """
        try:
            self.cursor.execute('''
                UPDATE redmine_tickets
                SET subject = ?, project = ?, status = ?, estimated_hours = ?, updated_on = ?, user = ?
                WHERE ticket_id = ?
            ''', (
                ticket_data.get("subject"),
                ticket_data.get("project"),
                ticket_data.get("status"),
                ticket_data.get("estimated_hours"),
                ticket_data.get("updated_on"),
                ticket_data.get("user"),
                ticket_data.get("ticket_id")
            ))
            self.conn.commit()
            logger.info("Ticket %s in der Datenbank aktualisiert.", ticket_data.get("ticket_id"))
        except Exception as error:
            logger.error("Fehler beim Aktualisieren des Tickets %s: %s", ticket_data.get("ticket_id"), error)

    def time_entry_exists(self, date_str: str, project: str, work_package: str, duration: float) -> bool:
        """
        Überprüft, ob ein Zeiteintrag mit den angegebenen Parametern bereits in der Tabelle work_log vorhanden ist.

        Args:
            date_str (str): Datum des Eintrags.
            project (str): Name des Projekts.
            work_package (str): Bezeichnung des Arbeitspakets.
            duration (float): Dauer des Eintrags.

        Returns:
            bool: True, wenn ein entsprechender Eintrag existiert, andernfalls False.
        """
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM work_log WHERE date=? AND project=? AND work_package=? AND duration=?",
                (date_str, project, work_package, duration)
            )
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as error:
            logger.error("Fehler bei der Überprüfung des Zeiteintrags: %s", error)
            return False

    def reset_database(self) -> None:
        """
        Setzt die Datenbank zurück, indem die bestehende Datenbankdatei gelöscht und die Verbindung neu initialisiert wird.
        """
        import os
        self.conn.close()
        if os.path.exists(self.DB_FILE):
            os.remove(self.DB_FILE)
        self.__init__()
        logger.info("Datenbank zurückgesetzt.")
