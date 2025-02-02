"""
@file config_manager.py
@brief Verwaltung der YAML-Konfiguration.
@version CHOE 02.02.2025
@details Diese Datei verwaltet das Laden und Speichern der YAML-Konfiguration, in der Projekte, Arbeitspakete und Backup-Daten hinterlegt sind.
"""

import os
import yaml
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    @brief Klasse zur Verwaltung der Konfiguration.
    @details Diese Klasse übernimmt das Laden, Speichern und Aktualisieren der Konfigurationsdaten in einer YAML-Datei.
    """
    CONFIG_FILE = "config.yaml"
    DEFAULT_CONFIG = {
        "projects": ["Projekt A", "Projekt B"],
        "work_packages": ["Entwicklung", "Meeting", "Design", "Testing", "Dokumentation"],
        "backup": {}
    }

    def __init__(self):
        """
        @brief Initialisiert den ConfigManager und lädt die Konfiguration.
        """
        self.config = self.load_config()

    def load_config(self):
        """
        @brief Lädt die Konfiguration aus der YAML-Datei.
        @return Konfigurations-Dictionary.
        """
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if config is None:
                        config = self.DEFAULT_CONFIG.copy()
                    for key in self.DEFAULT_CONFIG:
                        if key not in config:
                            config[key] = self.DEFAULT_CONFIG[key]
                    return config
            except Exception as e:
                logger.error("Fehler beim Laden der Konfiguration: %s", e)
                return self.DEFAULT_CONFIG.copy()
        else:
            self.save_config(self.DEFAULT_CONFIG.copy())
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, config):
        """
        @brief Speichert das Konfigurations-Dictionary in die YAML-Datei.
        @param config Das zu speichernde Konfigurations-Dictionary.
        """
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, allow_unicode=True)
            self.config = config
            logger.debug("Konfiguration gespeichert: %s", config)
        except Exception as e:
            logger.error("Fehler beim Speichern der Konfiguration: %s", e)

    def get_projects(self):
        """
        @brief Gibt die Liste der Projekte zurück.
        @return Liste der Projekte.
        """
        return self.config.get("projects", [])

    def get_work_packages(self):
        """
        @brief Gibt die Liste der Arbeitspakete zurück.
        @return Liste der Arbeitspakete.
        """
        return self.config.get("work_packages", [])

    def update_projects(self, projects):
        """
        @brief Aktualisiert die Projektliste.
        @param projects Neue Liste der Projekte.
        """
        self.config["projects"] = projects
        self.save_config(self.config)

    def update_work_packages(self, work_packages):
        """
        @brief Aktualisiert die Liste der Arbeitspakete.
        @param work_packages Neue Liste der Arbeitspakete.
        """
        self.config["work_packages"] = work_packages
        self.save_config(self.config)

    def get_backup(self):
        """
        @brief Gibt die aktuellen Backup-Daten zurück.
        @return Backup-Daten als Dictionary.
        """
        return self.config.get("backup", {})

    def update_backup(self, backup_data):
        """
        @brief Aktualisiert die Backup-Daten.
        @param backup_data Das Backup-Dictionary.
        """
        self.config["backup"] = backup_data
        self.save_config(self.config)

    def clear_backup(self):
        """
        @brief Löscht die Backup-Daten.
        """
        self.config["backup"] = {}
        self.save_config(self.config)
