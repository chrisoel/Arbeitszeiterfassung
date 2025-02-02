"""
@file plot_manager.py
@brief Verwaltung der Diagrammerstellung für die Zeiterfassung.
@version CHOE 02.02.2025
@details Diese Datei enthält Funktionen zur Erstellung von Diagrammen, wie beispielsweise zur durchschnittlichen Dauer pro Arbeitspaket
         und zur Häufigkeit der Zeiteinträge über die Zeit.
"""

import matplotlib.pyplot as plt
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class PlotManager:
    """
    @brief Klasse zur Erstellung von Diagrammen basierend auf den in der Datenbank gespeicherten Daten.
    """
    def __init__(self, db_manager):
        """
        @brief Initialisiert den PlotManager.
        @param db_manager Eine Instanz der Klasse DatabaseManager.
        """
        self.db_manager = db_manager

    def plot_average_duration(self, unit="Sekunden", selected_work_packages=None):
        """
        @brief Erstellt ein Balkendiagramm der durchschnittlichen Dauer pro Arbeitspaket.
        @param unit Zeiteinheit: "Sekunden", "Minuten" oder "Stunden".
        @param selected_work_packages Optionale Liste von Arbeitspaketen, die im Diagramm berücksichtigt werden sollen.
        @exception ValueError Falls keine Daten für die ausgewählten Arbeitspakete vorliegen.
        """
        rows = self.db_manager.fetch_avg_duration_per_work_package()
        if selected_work_packages:
            rows = [row for row in rows if row[0] in selected_work_packages]
        if not rows:
            raise ValueError("Keine Daten vorhanden für die ausgewählten Arbeitspakete.")
        work_packages = [row[0] for row in rows]
        avg_durations = [row[1] for row in rows]
        ylabel = "Durchschnittliche Dauer (Sekunden)"
        if unit == "Minuten":
            avg_durations = [d / 60 for d in avg_durations]
            ylabel = "Durchschnittliche Dauer (Minuten)"
        elif unit == "Stunden":
            avg_durations = [d / 3600 for d in avg_durations]
            ylabel = "Durchschnittliche Dauer (Stunden)"
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(work_packages, avg_durations, color="skyblue")
        ax.set_xlabel("Arbeitspaket")
        ax.set_ylabel(ylabel)
        ax.set_title("Durchschnittliche Dauer pro Arbeitspaket")
        fig.tight_layout()
        plt.show()
        logger.info("Plot 'Durchschnittliche Dauer' erstellt: Einheit=%s, Filter=%s", unit, selected_work_packages)

    def plot_work_package_frequency(self, selected_work_packages=None):
        """
        @brief Erstellt ein Diagramm, das die Häufigkeit der Zeiteinträge pro Tag für Arbeitspakete anzeigt.
        @param selected_work_packages Optionale Liste von Arbeitspaketen, die berücksichtigt werden sollen.
        @exception ValueError Falls keine Daten für die ausgewählten Arbeitspakete vorliegen.
        """
        data = self.db_manager.fetch_all_entries()
        if not data:
            raise ValueError("Keine Daten vorhanden.")
        df = pd.DataFrame(data, columns=["Datum", "Projekt", "Arbeitspaket", "Dauer"])
        df["Datum"] = pd.to_datetime(df["Datum"])
        df["Datum_only"] = df["Datum"].dt.date
        if selected_work_packages:
            df = df[df["Arbeitspaket"].isin(selected_work_packages)]
        freq = df.groupby(["Datum_only", "Arbeitspaket"]).size().reset_index(name="Count")
        if freq.empty:
            raise ValueError("Keine Daten vorhanden für die ausgewählten Arbeitspakete.")
        pivot = freq.pivot(index="Datum_only", columns="Arbeitspaket", values="Count").fillna(0)
        pivot.sort_index(inplace=True)
        fig, ax = plt.subplots(figsize=(10, 6))
        pivot.plot(kind="bar", stacked=True, ax=ax)
        ax.set_xlabel("Datum")
        ax.set_ylabel("Anzahl der Einträge")
        ax.set_title("Häufigkeit der Arbeitspakete über die Zeit")
        fig.tight_layout()
        plt.show()
        logger.info("Plot 'Häufigkeit' erstellt: Filter=%s", selected_work_packages)
