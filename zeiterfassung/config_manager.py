#!/usr/bin/env python
"""
config_manager.py
-----------------
Verwaltet Konfigurationsdaten in einer YAML-Datei.

Dieses Modul stellt die Klasse `ConfigurationManager` bereit, die für das Laden, Speichern und
Aktualisieren von Konfigurationen zuständig ist. Es werden Standardwerte verwendet, falls
die Konfigurationsdatei nicht existiert oder unvollständige Einstellungen vorliegen.

Version: CHOE 10.02.2025
"""

import os
import yaml
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Verwaltung der YAML-Konfiguration.

    Diese Klasse kapselt alle Operationen rund um das Laden, Speichern und Aktualisieren
    der Konfiguration, die in einer YAML-Datei abgelegt wird. Fehlende oder nicht existierende
    Einstellungen werden durch voreingestellte Standardwerte ersetzt.
    """

    CONFIG_FILE: str = "config.yaml"
    DEFAULT_CONFIG: Dict[str, Any] = {
        "projects": ["Projekt A", "Projekt B"],
        "work_packages": {},
        "backup": {},
        "REDMINE_URL": "",
        "REDMINE_BACKUP_PROJECT": "",
        "REDMINE_USER": "",
        "REDMINE_CREDENTIALS": None,
        "REDMINE_CONFIG_UPDATED": False,
    }

    def __init__(self) -> None:
        """
        Initialisiert den ConfigurationManager.

        Beim Erstellen eines Objekts dieser Klasse wird die Konfiguration automatisch aus der
        YAML-Datei geladen. Sollte die Datei nicht vorhanden oder unvollständig sein, werden
        die Standardwerte verwendet und die Datei wird erzeugt.
        """
        self.config: Dict[str, Any] = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Lädt die Konfiguration aus der YAML-Datei.

        Wenn die Datei existiert, wird sie geöffnet und der Inhalt wird mittels YAML-Parser
        eingelesen. Fehlende Schlüssel werden automatisch mit den Standardwerten ergänzt.
        Tritt ein Fehler beim Laden auf, wird die Standardkonfiguration zurückgegeben.

        Returns:
            Dict[str, Any]: Ein Dictionary mit allen Konfigurationseinstellungen.
        """
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_config = yaml.safe_load(f) or {}
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                return loaded_config
            except Exception as error:
                logger.error("Fehler beim Laden der Konfiguration: %s", error)
                return self.DEFAULT_CONFIG.copy()
        else:
            self.save_config(self.DEFAULT_CONFIG.copy())
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Speichert die übergebene Konfiguration in der YAML-Datei.

        Nach erfolgreichem Speichern wird die interne Konfiguration aktualisiert.

        Args:
            config (Dict[str, Any]): Das Konfigurations-Dictionary, das gespeichert werden soll.
        """
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, allow_unicode=True)
            self.config = config
            logger.debug("Konfiguration erfolgreich gespeichert.")
        except Exception as error:
            logger.error("Fehler beim Speichern der Konfiguration: %s", error)

    def get_projects(self) -> List[str]:
        """
        Gibt die Liste der Projekte aus der Konfiguration zurück.

        Returns:
            List[str]: Eine Liste von Projektnamen.
        """
        return self.config.get("projects", [])

    def update_projects(self, projects: List[str]) -> None:
        """
        Aktualisiert die Liste der Projekte und speichert die Änderung.

        Args:
            projects (List[str]): Eine Liste der neuen Projektnamen.
        """
        self.config["projects"] = projects
        self.save_config(self.config)

    def get_work_packages(self) -> Dict[str, Any]:
        """
        Ruft die Zuordnung der Arbeitsaufgaben (Work Packages) ab.

        Returns:
            Dict[str, Any]: Ein Dictionary, das Projektnamen auf ihre zugehörigen
                            Arbeitsaufgaben abbildet.
        """
        return self.config.get("work_packages", {})

    def update_work_packages(self, work_packages: Dict[str, Any]) -> None:
        """
        Aktualisiert die Zuordnung der Arbeitsaufgaben in der Konfiguration und speichert die Änderung.

        Args:
            work_packages (Dict[str, Any]): Ein Dictionary mit den neuen Zuordnungen der Arbeitsaufgaben.
        """
        self.config["work_packages"] = work_packages
        self.save_config(self.config)

    def get_backup(self) -> Dict[str, Any]:
        """
        Gibt die Backup-Daten aus der Konfiguration zurück.

        Returns:
            Dict[str, Any]: Ein Dictionary, das die aktuellen Backup-Daten enthält.
        """
        return self.config.get("backup", {})

    def update_backup(self, backup_data: Dict[str, Any]) -> None:
        """
        Aktualisiert die Backup-Daten in der Konfiguration und speichert die Änderung.

        Args:
            backup_data (Dict[str, Any]): Ein Dictionary mit den neuen Backup-Daten.
        """
        self.config["backup"] = backup_data
        self.save_config(self.config)

    def clear_backup(self) -> None:
        """
        Löscht alle Backup-Daten aus der Konfiguration und speichert die Änderung.
        """
        self.config["backup"] = {}
        self.save_config(self.config)

    def reset_config(self) -> None:
        """
        Setzt die gesamte Konfiguration auf die Standardwerte zurück und speichert diese Änderung.
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config(self.config)
