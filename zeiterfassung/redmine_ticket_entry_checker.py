#!/usr/bin/env python
"""
redmine_ticket_entry_checker.py
---------------------------------
Überprüfung der Zeiteinträge pro Ticket auf Redmine.

Dieses Modul verbindet sich mit dem Redmine-Server, aktualisiert (falls noch nicht geschehen)
die lokale Konfiguration (Projekte und Tickets) und gibt anschließend alle Tickets mit deren Zeiteinträgen aus.

Version: CHOE 10.02.2025
"""

import logging
from config_manager import ConfigurationManager
from redmine_manager import RedmineManager


def main() -> None:
    """
    Hauptfunktion des Redmine Ticket & Zeiteintrag Checkers.

    Diese Funktion initialisiert die Konfiguration und den RedmineManager, stellt eine Verbindung zum Redmine-Server her,
    aktualisiert die lokale Konfiguration (Projekte und Tickets) und überprüft die Zeiteinträge pro Ticket der erlaubten Projekte.
    """
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Starte Redmine Ticket & Zeiteintrag Checker")

    config_manager = ConfigurationManager()
    redmine_manager = RedmineManager(config_manager.config)

    if not redmine_manager.connect():
        logger.error("Verbindung zu Redmine konnte nicht hergestellt werden.")
        return

    redmine_manager.update_config_with_projects_and_tickets(config_manager)

    allowed_project_names = config_manager.config.get("projects", [])
    logger.info("Erlaubte Projekte laut Konfiguration: %s", allowed_project_names)

    try:
        all_projects = redmine_manager.redmine.project.all()
    except Exception as error:
        logger.error("Fehler beim Abrufen aller Projekte: %s", error)
        return

    allowed_projects = [proj for proj in all_projects if proj.name in allowed_project_names]
    logger.info("Es werden %d Projekte überprüft.", len(allowed_projects))

    for project in allowed_projects:
        logger.info("Verarbeite Projekt: %s (ID: %s)", project.name, project.id)
        try:
            tickets = redmine_manager.redmine.issue.filter(project_id=project.id)
            logger.info("Projekt '%s' enthält %d Tickets.", project.name, len(tickets))
            for ticket in tickets:
                logger.debug("--------------------------------------------------")
                logger.debug("Ticket ID      : %s", ticket.id)
                logger.debug("Subject        : %s", ticket.subject)
                logger.debug("Status         : %s", ticket.status.name)
                logger.debug("Estimated Hrs  : %s", getattr(ticket, 'estimated_hours', None))
                logger.debug("Updated On     : %s", ticket.updated_on)
                try:
                    time_entries = redmine_manager.redmine.time_entry.filter(issue_id=ticket.id)
                    logger.info("Ticket %s hat %d Zeiteinträge.", ticket.id, len(time_entries))
                    for entry in time_entries:
                        logger.debug("  Zeiteintrag: Spent On: %s, Hours: %.2f", entry.spent_on, entry.hours)
                except Exception as error:
                    logger.error("Fehler beim Abrufen der Zeiteinträge für Ticket %s: %s", ticket.id, error)
        except Exception as error:
            logger.error("Fehler beim Abrufen der Tickets für Projekt '%s': %s", project.name, error)
            continue

    logger.info("Redmine Ticket & Zeiteintrag Checker abgeschlossen.")


if __name__ == '__main__':
    main()
