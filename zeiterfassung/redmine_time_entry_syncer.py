#!/usr/bin/env python
"""
redmine_time_entry_syncer.py
----------------------------
Synchronisiert Zeiteinträge aus Redmine in die lokale Datenbank.

Dieses Modul verbindet sich mit dem Redmine-Server, aktualisiert die lokale Konfiguration
(Projekte und Tickets) und überträgt alle Zeiteinträge des aktuell angemeldeten Nutzers in die lokale Datenbank.
Doppelte Einträge werden vermieden.

Version: CHOE 10.02.2025
"""

import logging
from config_manager import ConfigurationManager
from redmine_manager import RedmineManager
from database_manager import DatabaseManager


def main() -> None:
    """
    Hauptfunktion des Redmine Time Entry Syncers.

    Diese Funktion initialisiert die Konfiguration, den Redmine-Manager und den Datenbankmanager.
    Anschließend wird versucht, eine Verbindung zum Redmine-Server herzustellen. Bei erfolgreicher Verbindung
    wird die Konfiguration (Projekte und Tickets) aktualisiert und alle Zeiteinträge des aktuell angemeldeten Nutzers
    in die lokale Datenbank synchronisiert.
    """
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Starte Redmine Time Entry Syncer")

    config_manager = ConfigurationManager()
    redmine_manager = RedmineManager(config_manager.config)
    db_manager = DatabaseManager()

    if not redmine_manager.connect():
        logger.error("Verbindung zu Redmine konnte nicht hergestellt werden.")
        return

    redmine_manager.update_config_with_projects_and_tickets(config_manager)
    redmine_manager.sync_time_entries(db_manager)

    logger.info("Redmine Time Entry Sync abgeschlossen.")


if __name__ == '__main__':
    main()
