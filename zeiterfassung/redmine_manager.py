#!/usr/bin/env python
"""
redmine_manager.py
------------------
Integration mit Redmine für die Zeiterfassung.

Dieses Modul stellt Funktionen zum Verbinden mit dem Redmine-Server, zum Erstellen bzw. Aktualisieren
eines Zeiterfassungstickets im Backup-Projekt, zur Synchronisation der Redmine-Ticket- und Zeiteintragsdaten
in die SQL-Datenbank sowie zur Aktualisierung der Konfiguration (Projekte und Tickets) bereit.

Version: CHOE 10.02.2025
"""

import logging
import base64
import math
from redminelib import Redmine
from tkinter import simpledialog, messagebox

logger = logging.getLogger(__name__)


def encrypt_credentials(username: str, password: str) -> str:
    """
    Verschlüsselt die Anmeldedaten mittels Base64.

    Hinweis: Diese Methode bietet keine echte Sicherheit und dient nur als Beispiel.

    Args:
        username (str): Der Redmine-Benutzername.
        password (str): Das zugehörige Passwort.

    Returns:
        str: Der verschlüsselte Anmeldedatenstring.
    """
    combined = f"{username}:{password}"
    encoded = base64.b64encode(combined.encode("utf-8")).decode("utf-8")
    return encoded


def decrypt_credentials(enc_string: str) -> tuple:
    """
    Entschlüsselt die verschlüsselten Anmeldedaten.

    Args:
        enc_string (str): Der verschlüsselte Anmeldedatenstring.

    Returns:
        tuple: Ein Tupel (username, password) der entschlüsselten Daten.
    """
    decoded = base64.b64decode(enc_string.encode("utf-8")).decode("utf-8")
    username, password = decoded.split(":", 1)
    return username, password


class RedmineManager:
    """
    Integration mit Redmine für die Zeiterfassung.

    Diese Klasse stellt Methoden bereit, um eine Verbindung mit dem Redmine-Server herzustellen,
    Zeiteinträge als Tickets im Backup-Projekt zu erstellen oder zu aktualisieren, und
    die Synchronisation von Redmine-Ticketdaten und Zeiteinträgen mit einer lokalen SQL-Datenbank
    durchzuführen. Zusätzlich wird die Konfiguration mit Projekten und Tickets aktualisiert.
    """

    def __init__(self, config: dict) -> None:
        """
        Initialisiert den RedmineManager.

        Args:
            config (dict): Das Konfigurations-Dictionary, z. B. aus dem ConfigurationManager.
        """
        self.config = config
        self.redmine_url = config.get("REDMINE_URL", "")
        self.backup_project = config.get("REDMINE_BACKUP_PROJECT", "")
        self.redmine = None

    def connect(self) -> bool:
        """
        Baut die Verbindung zum Redmine-Server auf.

        Falls gespeicherte Anmeldedaten vorhanden sind, wird der Benutzer gefragt, ob diese verwendet werden sollen.
        Ansonsten wird der Benutzer zur Eingabe von Benutzername und Passwort aufgefordert. Die Methode versucht bis zu
        drei Mal, eine Verbindung herzustellen.

        Returns:
            bool: True, wenn die Verbindung hergestellt werden konnte, sonst False.
        """
        if not self.redmine_url:
            logger.warning("Keine REDMINE_URL in der Konfiguration hinterlegt.")
            return False

        attempts = 0
        max_attempts = 3

        if self.config.get("REDMINE_CREDENTIALS"):
            use_stored = messagebox.askyesno("Anmeldedaten", "Möchten Sie Ihre gespeicherten Anmeldedaten verwenden?")
            if use_stored:
                try:
                    username, password = decrypt_credentials(self.config["REDMINE_CREDENTIALS"])
                    self.redmine = Redmine(self.redmine_url, username=username, password=password)
                    _ = self.redmine.user.get('current')
                    logger.info("Erfolgreich mit Redmine verbunden (gespeicherte Daten).")
                    return True
                except Exception as error:
                    logger.error("Fehler bei Verwendung der gespeicherten Anmeldedaten: %s", error)

        while attempts < max_attempts:
            username = simpledialog.askstring("Redmine Login", "Bitte geben Sie Ihren Redmine Benutzernamen ein:")
            if username is None:
                attempts += 1
                continue

            password = simpledialog.askstring("Redmine Login", "Bitte geben Sie Ihr Redmine Passwort ein:", show="*")
            if password is None:
                attempts += 1
                continue

            try:
                self.redmine = Redmine(self.redmine_url, username=username, password=password)
                _ = self.redmine.user.get('current')
                logger.info("Erfolgreich mit Redmine verbunden.")
                store = messagebox.askyesno("Anmeldedaten speichern", "Möchten Sie Ihre Anmeldedaten verschlüsselt speichern?")
                if store:
                    self.config["REDMINE_CREDENTIALS"] = encrypt_credentials(username, password)
                return True
            except Exception as error:
                attempts += 1
                logger.error("Fehler beim Verbinden mit Redmine (Versuch %d von %d): %s", attempts, max_attempts, error)
                messagebox.showerror("Redmine Login", f"Anmeldung fehlgeschlagen. Versuch {attempts} von {max_attempts}.")

        messagebox.showerror("Redmine Login", "Maximale Anzahl an Versuchen erreicht. Bitte starten Sie die App neu.")
        return False

    def create_time_entry(self, original_project: str, work_package: str, duration: float, date_str: str):
        """
        Erstellt oder aktualisiert ein Zeiterfassungsticket im Backup-Projekt.

        Die Methode ermittelt anhand des übergebenen Arbeitspakets das zugehörige Ticket, berechnet die Zeit in Stunden,
        rundet diese auf das nächste Viertelstundentakt auf und fügt entweder einen neuen Zeiteintrag zu einem vorhandenen
        Ticket hinzu oder erstellt ein neues Ticket mit dem Zeiteintrag.

        Args:
            original_project (str): Der ursprüngliche Projektname.
            work_package (str): Das Arbeitspaket bzw. Ticketkennzeichen.
            duration (float): Die Dauer in Sekunden.
            date_str (str): Das Datum des Eintrags im Format YYYY-MM-DD.

        Returns:
            Das erstellte oder aktualisierte Ticket oder None im Fehlerfall.
        """
        if not self.redmine:
            logger.error("Keine Redmine-Verbindung vorhanden.")
            return None
        if not self.backup_project:
            logger.error("Kein Backup-Projekt in der Konfiguration hinterlegt.")
            return None

        try:
            ticket_number = work_package.split(":")[0].strip() if ":" in work_package else work_package
            subject = f"{original_project} - Ticket {ticket_number}"
            raw_hours = duration / 3600.0
            rounded_hours = max(math.ceil(raw_hours * 4) / 4.0, 0.25)
            description = (f"Erfasste Dauer: {duration} Sekunden ({rounded_hours:.2f} Stunden)\n"
                           f"Projekt: {original_project}\n"
                           f"Ticket: {ticket_number}")

            projects = self.redmine.project.all()
            backup_project_id = None
            for proj in projects:
                if proj.name == self.backup_project:
                    backup_project_id = proj.id
                    break
            if not backup_project_id:
                logger.error("Backup-Projekt '%s' nicht gefunden.", self.backup_project)
                return None

            try:
                existing_issues = self.redmine.issue.filter(project_id=backup_project_id, subject=subject)
            except Exception as error:
                logger.error("Fehler beim Suchen nach bestehendem Ticket: %s", error)
                existing_issues = []

            if existing_issues:
                issue = existing_issues[0]
                try:
                    self.redmine.time_entry.create(
                        issue_id=issue.id,
                        spent_on=date_str,
                        hours=rounded_hours,
                        comments="Zusätzlicher Zeiteintrag"
                    )
                    logger.info("Zeitaufwand zu bestehendem Ticket hinzugefügt: %s", subject)
                except Exception as error:
                    logger.error("Fehler beim Hinzufügen des Zeitaufwands: %s", error)
                return issue
            else:
                try:
                    issue = self.redmine.issue.create(
                        project_id=backup_project_id,
                        subject=subject,
                        description=description,
                        estimated_hours=rounded_hours
                    )
                    logger.info("Neues Zeiterfassungsticket in Redmine erstellt: %s", subject)
                    self.redmine.time_entry.create(
                        issue_id=issue.id,
                        spent_on=date_str,
                        hours=rounded_hours,
                        comments="Erster Zeiteintrag"
                    )
                    logger.info("Zeitaufwand zum neuen Ticket hinzugefügt: %s", subject)
                    return issue
                except Exception as error:
                    logger.error("Fehler beim Erstellen des Tickets oder Hinzufügen des Zeitaufwands: %s", error)
                    return None
        except Exception as outer_error:
            logger.error("Allgemeiner Fehler in create_time_entry: %s", outer_error)
            return None

    def sync_my_tickets(self, db_manager) -> None:
        """
        Synchronisiert die Redmine-Tickets des aktuellen Nutzers in die SQL-Datenbank.

        Die Methode aktualisiert das Konfigurations-Dictionary mit dem aktuellen Redmine-Benutzer,
        ruft alle dem Benutzer zugewiesenen Tickets ab und aktualisiert oder fügt diese in der Datenbank ein.

        Args:
            db_manager: Eine Instanz des Datenbankmanagers zur Verwaltung der SQL-Datenbank.
        """
        if not self.config.get("REDMINE_USER"):
            try:
                current_user = self.redmine.user.get('current')
                self.config["REDMINE_USER"] = current_user.login
            except Exception as error:
                logger.error("Fehler beim Abrufen des aktuellen Nutzers: %s", error)
                return

        my_user = self.config["REDMINE_USER"]
        try:
            issues = self.redmine.issue.filter(assigned_to_id='me')
        except Exception as error:
            logger.error("Fehler beim Abrufen der Tickets: %s", error)
            return

        for issue in issues:
            ticket_data = {
                "ticket_id": issue.id,
                "subject": issue.subject,
                "project": issue.project.name,
                "status": issue.status.name,
                "estimated_hours": getattr(issue, 'estimated_hours', None),
                "updated_on": issue.updated_on,
                "user": my_user
            }
            if db_manager.ticket_exists(issue.id):
                db_manager.update_ticket(ticket_data)
                logger.info("Ticket %s aktualisiert.", issue.id)
            else:
                db_manager.insert_ticket(ticket_data)
                logger.info("Ticket %s synchronisiert.", issue.id)

    def sync_time_entries(self, db_manager) -> None:
        """
        Synchronisiert alle Zeiteinträge des aktuellen Nutzers aus Redmine in die lokale SQL-Datenbank.

        Die Methode ruft alle Zeiteinträge des Nutzers ab, berechnet die gerundeten Stunden,
        ermittelt das zugehörige Ticket und fügt den Eintrag in die Datenbank ein, sofern dieser noch nicht existiert.

        Args:
            db_manager: Eine Instanz des Datenbankmanagers zur Verwaltung der SQL-Datenbank.
        """
        try:
            time_entries = self.redmine.time_entry.filter(user_id='me')
        except Exception as error:
            logger.error("Fehler beim Abrufen der Zeiteinträge: %s", error)
            return

        for entry in time_entries:
            try:
                if not hasattr(entry, 'spent_on'):
                    logger.error("Zeiteintrag besitzt kein 'spent_on'-Attribut. Verfügbare Attribute: %s", dir(entry))
                    continue
                date_str = entry.spent_on
                if not hasattr(entry, 'hours'):
                    logger.error("Zeiteintrag besitzt kein 'hours'-Attribut. Verfügbare Attribute: %s", dir(entry))
                    continue
                hours = entry.hours
                rounded_hours = max(math.ceil(hours * 4) / 4.0, 0.25)
                try:
                    issue = entry.issue
                except AttributeError:
                    if hasattr(entry, 'issue_id'):
                        issue = self.redmine.issue.get(entry.issue_id)
                    else:
                        logger.error("Zeiteintrag besitzt weder 'issue' noch 'issue_id'. Verfügbare Attribute: %s", dir(entry))
                        continue
                project = issue.project.name
                work_package = f"{issue.id}: {issue.subject}"
                duration_seconds = rounded_hours * 3600
                if not db_manager.time_entry_exists(date_str, project, work_package, duration_seconds):
                    db_manager.record_time_entry(date_str, project, work_package, duration_seconds)
                    logger.info("Zeiteintrag synchronisiert: Datum: %s, Projekt: %s, Ticket: %s, %.2f h",
                                date_str, project, work_package, rounded_hours)
            except Exception as error:
                logger.error("Fehler beim Synchronisieren eines Zeiteintrags: %s", error)
                continue

    def update_config_with_projects_and_tickets(self, config_manager) -> None:
        """
        Aktualisiert die Konfiguration mit den Redmine-Projekten und deren Tickets.

        Falls die Konfiguration bereits aktualisiert wurde, wird die Aktualisierung übersprungen.
        Andernfalls werden alle Projekte (außer dem Backup-Projekt) und die zugehörigen Tickets abgerufen
        und in das Konfigurations-Dictionary übernommen.

        Args:
            config_manager: Eine Instanz des Konfigurationsmanagers zur Aktualisierung der Konfiguration.
        """
        if self.config.get("REDMINE_CONFIG_UPDATED"):
            logger.info("Redmine-Konfiguration wurde bereits aktualisiert. Überspringe Aktualisierung.")
            return

        try:
            projects = self.redmine.project.all()
        except Exception as error:
            logger.error("Fehler beim Abrufen der Projekte: %s", error)
            return

        updated_projects = set(config_manager.config.get("projects", []))
        updated_work_packages = config_manager.config.get("work_packages", {})
        backup_proj = self.config.get("REDMINE_BACKUP_PROJECT", "")

        for project in projects:
            if project.name == backup_proj:
                logger.info("Projekt '%s' entspricht dem Backup-Projekt. Überspringe.", project.name)
                continue
            try:
                issues = self.redmine.issue.filter(project_id=project.id)
                ticket_list = []
                for issue in issues:
                    ticket_str = f"{issue.id}: {issue.subject}"
                    ticket_list.append(ticket_str)
                existing = set(updated_work_packages.get(project.name, []))
                updated_work_packages[project.name] = sorted(existing.union(ticket_list))
                updated_projects.add(project.name)
            except Exception as error:
                logger.error("Fehler beim Abrufen der Tickets für Projekt '%s': %s. Überspringe dieses Projekt.", project.name, error)
                continue

        config_manager.config["projects"] = sorted(updated_projects)
        config_manager.config["work_packages"] = updated_work_packages
        config_manager.config["REDMINE_CONFIG_UPDATED"] = True
        config_manager.save_config(config_manager.config)
        logger.info("Konfiguration mit Projekten und Tickets aktualisiert.")
