#!/usr/bin/env python
"""
time_tracker_app.py
-------------------
Hauptanwendung der Zeiterfassung.

Dieses Modul integriert alle Komponenten (Konfiguration, Datenbank, Plot, Dialoge, Redmine) und
stellt die Benutzeroberfläche zur Zeiterfassung bereit.

Version: CHOE 10.02.2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
from datetime import datetime, date
import pandas as pd
import logging
import math
import sys, os

from config_manager import ConfigurationManager
from database_manager import DatabaseManager
from plot_manager import PlotManager
from dialogs import BackupChoiceDialog, ClosePromptDialog

logger = logging.getLogger(__name__)


def format_time(seconds: float) -> str:
    """
    Formatiert eine Zeitangabe in Sekunden als HH:MM:SS-Format.

    Args:
        seconds (float): Die zu formatierende Zeit in Sekunden.

    Returns:
        str: Die formatierte Zeit als Zeichenkette.
    """
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class TimeTrackerApp:
    """
    Hauptanwendung der Zeiterfassung.

    Diese Klasse integriert die Konfiguration, Datenbank, Diagrammerstellung, Dialoge und Redmine-Integration.
    Sie stellt die grafische Benutzeroberfläche zur Zeiterfassung bereit und verwaltet Timer, Backups und Datenexport.
    """

    def __init__(self, master: tk.Tk) -> None:
        """
        Initialisiert die Zeiterfassungsanwendung und richtet die Benutzeroberfläche sowie alle Komponenten ein.

        Args:
            master (tk.Tk): Das Haupt-Tkinter-Fenster.
        """
        self.master = master
        self.master.title("Zeiterfassung")
        logger.info("Zeiterfassung gestartet.")
        self.config_manager = ConfigurationManager()
        self.db_manager = DatabaseManager()
        self.plot_manager = PlotManager(self.db_manager)
        self.elapsed_time = 0.0
        self.running = False
        self.start_time = None
        self.update_job = None

        self.create_widgets()

        from redmine_manager import RedmineManager
        redmine_url = self.config_manager.config.get("REDMINE_URL", "")
        if not redmine_url:
            redmine_url = simpledialog.askstring("Redmine URL", "Bitte geben Sie Ihre Redmine URL ein:")
            if redmine_url:
                self.config_manager.config["REDMINE_URL"] = redmine_url
                self.config_manager.save_config(self.config_manager.config)
        self.redmine_manager = RedmineManager(self.config_manager.config)
        if self.redmine_manager.connect():
            self.redmine_manager.update_config_with_projects_and_tickets(self.config_manager)
            projects = self.config_manager.config.get("projects", [])
            self.project_combobox['values'] = projects
            if projects:
                self.project_combobox.set(projects[0])
            self.update_work_packages_for_project()
            if not self.config_manager.config.get("REDMINE_USER"):
                try:
                    current_user = self.redmine_manager.redmine.user.get('current')
                    self.config_manager.config["REDMINE_USER"] = current_user.login
                    self.config_manager.save_config(self.config_manager.config)
                    logger.info("Aktueller Redmine-Nutzer: %s", current_user.login)
                except Exception as error:
                    logger.error("Fehler beim Abrufen des aktuellen Nutzers: %s", error)
            backup_project = self.config_manager.config.get("REDMINE_BACKUP_PROJECT", "")
            if not backup_project:
                backup_project = self.choose_backup_project()
                if backup_project:
                    self.config_manager.config["REDMINE_BACKUP_PROJECT"] = backup_project
                    self.config_manager.save_config(self.config_manager.config)
            self.redmine_manager.sync_my_tickets(self.db_manager)
            self.redmine_manager.sync_time_entries(self.db_manager)
        else:
            messagebox.showerror("Redmine-Login", "Redmine-Anmeldung fehlgeschlagen. Bitte starten Sie die App neu und versuchen Sie es erneut.")

        self.check_for_backup()
        self.auto_backup()
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def choose_backup_project(self) -> str:
        """
        Öffnet einen Dialog zur Auswahl des Backup-Projekts und gibt den Namen des ausgewählten Projekts zurück.

        Returns:
            str: Der Name des ausgewählten Backup-Projekts oder ein leerer String, falls keine Auswahl getroffen wurde.
        """
        try:
            projects = self.redmine_manager.redmine.project.all()
        except Exception as error:
            logger.error("Fehler beim Abrufen der Projekte: %s", error)
            messagebox.showerror("Fehler", "Projekte konnten nicht abgerufen werden.")
            return ""
        dlg = tk.Toplevel(self.master)
        dlg.title("Backup-Projekt auswählen")
        tk.Label(dlg, text="Bitte wählen Sie Ihr Backup-Projekt aus:").pack(padx=10, pady=10)
        lb = tk.Listbox(dlg, width=50, height=10)
        lb.pack(padx=10, pady=10)
        project_dict = {}
        for project in projects:
            display_text = f"{project.id}: {project.name}"
            lb.insert(tk.END, display_text)
            project_dict[display_text] = project.name

        selected_project = {"name": None}

        def choose() -> None:
            sel = lb.curselection()
            if sel:
                sel_text = lb.get(sel[0])
                selected_project["name"] = project_dict[sel_text]
                dlg.destroy()
            else:
                messagebox.showwarning("Warnung", "Bitte wählen Sie ein Projekt aus.")

        tk.Button(dlg, text="Auswählen", command=choose).pack(pady=10)
        dlg.grab_set()
        self.master.wait_window(dlg)
        return selected_project["name"] if selected_project["name"] else ""

    def update_work_packages_for_project(self) -> None:
        """
        Aktualisiert die Liste der Arbeitspakete basierend auf dem ausgewählten Projekt.
        """
        selected_project = self.project_combobox.get().strip()
        wp_dict = self.config_manager.get_work_packages()
        wp_list = wp_dict.get(selected_project, [])
        self.work_package_combobox['values'] = wp_list
        if wp_list:
            self.work_package_combobox.set(wp_list[0])
        else:
            self.work_package_combobox.set("")

    def create_widgets(self) -> None:
        """
        Erstellt und platziert alle grafischen Benutzeroberflächenelemente der Anwendung.
        """
        top_frame = tk.Frame(self.master)
        top_frame.grid(row=0, column=0, columnspan=4, pady=10)
        self.timer_label = tk.Label(top_frame, text="00:00:00", font=("Helvetica", 32))
        self.timer_label.pack(side=tk.LEFT, padx=10)
        self.forecast_label = tk.Label(top_frame, text="Geschätzte Zeit: -", font=("Helvetica", 16))
        self.forecast_label.pack(side=tk.LEFT, padx=10)
        self.start_button = tk.Button(self.master, text="Start", width=10, command=self.start_timer)
        self.start_button.grid(row=1, column=0, padx=5, pady=5)
        self.pause_button = tk.Button(self.master, text="Pause", width=10, command=self.pause_timer)
        self.pause_button.grid(row=1, column=1, padx=5, pady=5)
        self.record_button = tk.Button(self.master, text="Erfassen", width=10, command=self.record_time)
        self.record_button.grid(row=1, column=2, padx=5, pady=5)
        self.quit_button = tk.Button(self.master, text="Beenden", width=10, command=self.on_close)
        self.quit_button.grid(row=1, column=3, padx=5, pady=5)
        tk.Label(self.master, text="Projekt:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.project_combobox = ttk.Combobox(self.master, state="readonly", width=27)
        self.project_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.project_combobox['values'] = self.config_manager.config.get("projects", [])
        if self.config_manager.config.get("projects", []):
            self.project_combobox.set(self.config_manager.config.get("projects", [])[0])
        self.project_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_work_packages_for_project())
        tk.Button(self.master, text="Verwalten", command=self.manage_projects).grid(row=2, column=2, padx=5, pady=5)
        tk.Label(self.master, text="Arbeitspaket (Ticket):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.work_package_combobox = ttk.Combobox(self.master, state="readonly", width=27)
        self.work_package_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.update_work_packages_for_project()
        self.work_package_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_forecast())
        tk.Button(self.master, text="Verwalten", command=self.manage_work_packages).grid(row=3, column=2, padx=5, pady=5)
        self.export_button = tk.Button(self.master, text="Export nach Excel", command=self.export_to_excel)
        self.export_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.plot_button = tk.Button(self.master, text="Plot anzeigen", command=self.show_plot_options)
        self.plot_button.grid(row=4, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
        self.today_button = tk.Button(self.master, text="Heute anzeigen", command=self.show_today_data)
        self.today_button.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        settings_frame = tk.Frame(self.master)
        settings_frame.grid(row=6, column=0, columnspan=4, pady=10)
        tk.Button(settings_frame, text="Redmine URL ändern", command=self.change_redmine_url).pack(side=tk.LEFT, padx=10)
        tk.Button(settings_frame, text="Backup-Projekt ändern", command=self.change_backup_project).pack(side=tk.LEFT, padx=10)
        tk.Button(settings_frame, text="Sync Redmine Tickets", command=self.sync_redmine_tickets).pack(side=tk.LEFT, padx=10)
        tk.Button(settings_frame, text="App zurücksetzen", command=self.reset_app).pack(side=tk.LEFT, padx=10)
        self.update_forecast()

    def change_redmine_url(self) -> None:
        """
        Erlaubt dem Benutzer, die Redmine URL zu ändern und stellt eine neue Verbindung her.

        Fragt die neue URL ab, aktualisiert die Konfiguration, stellt eine Verbindung her und aktualisiert
        die Projekt- und Arbeitspaketlisten.
        """
        new_url = simpledialog.askstring("Redmine URL", "Bitte geben Sie Ihre neue Redmine URL ein:")
        if not new_url:
            return
        from redmine_manager import RedmineManager
        self.config_manager.config["REDMINE_URL"] = new_url
        self.redmine_manager = RedmineManager(self.config_manager.config)
        while not self.redmine_manager.connect():
            messagebox.showerror("Fehler", "Die eingegebene Redmine URL ist ungültig. Bitte versuchen Sie es erneut.")
            new_url = simpledialog.askstring("Redmine URL", "Bitte geben Sie Ihre neue Redmine URL ein:")
            if not new_url:
                return
            self.config_manager.config["REDMINE_URL"] = new_url
            self.redmine_manager = RedmineManager(self.config_manager.config)
        messagebox.showinfo("Erfolg", "Redmine URL wurde aktualisiert und Verbindung hergestellt.")
        self.config_manager.save_config(self.config_manager.config)
        self.redmine_manager.update_config_with_projects_and_tickets(self.config_manager)
        projects = self.config_manager.config.get("projects", [])
        self.project_combobox['values'] = projects
        if projects:
            self.project_combobox.set(projects[0])
        self.update_work_packages_for_project()
        self.redmine_manager.sync_my_tickets(self.db_manager)

    def change_backup_project(self) -> None:
        """
        Ermöglicht dem Benutzer, das Backup-Projekt zu ändern.

        Öffnet einen Dialog zur Auswahl des Backup-Projekts und aktualisiert die Konfiguration.
        """
        if not (hasattr(self, 'redmine_manager') and self.redmine_manager.redmine):
            messagebox.showerror("Fehler", "Keine gültige Redmine Verbindung vorhanden.")
            return
        backup_project = self.choose_backup_project()
        if backup_project:
            self.config_manager.config["REDMINE_BACKUP_PROJECT"] = backup_project
            self.config_manager.save_config(self.config_manager.config)
            messagebox.showinfo("Erfolg", f"Backup-Projekt wurde auf '{backup_project}' aktualisiert.")

    def sync_redmine_tickets(self) -> None:
        """
        Synchronisiert Redmine-Tickets und Zeiteinträge mit der lokalen Datenbank.

        Ruft die Methoden zur Synchronisation der Tickets und Zeiteinträge auf und zeigt eine Erfolgsmeldung an.
        """
        if hasattr(self, 'redmine_manager') and self.redmine_manager.redmine:
            self.redmine_manager.sync_my_tickets(self.db_manager)
            self.redmine_manager.sync_time_entries(self.db_manager)
            messagebox.showinfo("Erfolg", "Redmine Tickets und Zeiteinträge wurden synchronisiert.")
        else:
            messagebox.showerror("Fehler", "Keine gültige Redmine Verbindung vorhanden.")

    def reset_app(self) -> None:
        """
        Setzt die Anwendung zurück.

        Bestätigt mit dem Benutzer, löscht alle Einstellungen und Daten, und startet die App neu.
        """
        if messagebox.askyesno("App zurücksetzen", "Möchten Sie die App wirklich zurücksetzen? Alle Einstellungen und Daten werden gelöscht. Die App startet danach neu."):
            self.config_manager.reset_config()
            self.db_manager.reset_database()
            logger.info("App wird neu gestartet...")
            os.execv(sys.executable, [sys.executable] + sys.argv)

    def update_forecast(self) -> None:
        """
        Aktualisiert die Schätzung der durchschnittlichen Zeit basierend auf den erfassten Daten.

        Ruft den Durchschnittswert für das ausgewählte Projekt und Arbeitspaket ab und aktualisiert
        die Anzeige mit der geschätzten Zeit in Stunden.
        """
        project = self.project_combobox.get().strip()
        work_package = self.work_package_combobox.get().strip()
        if not project or not work_package:
            self.forecast_label.config(text="Geschätzte Zeit: -")
            return
        avg_seconds = self.db_manager.fetch_avg_duration_for(project, work_package)
        if avg_seconds == 0:
            self.forecast_label.config(text="Geschätzte Zeit: Keine Daten")
            return
        avg_hours = avg_seconds / 3600
        rounded_hours = math.ceil(avg_hours * 4) / 4
        self.forecast_label.config(text=f"Geschätzte Zeit: {rounded_hours:.2f} Stunden")

    def start_timer(self) -> None:
        """
        Startet den Timer, sofern er nicht bereits läuft.
        """
        if not self.running:
            self.running = True
            self.start_time = time.time()
            logger.info("Timer gestartet.")
            self.update_timer()

    def update_timer(self) -> None:
        """
        Aktualisiert die Anzeige des Timers periodisch, solange der Timer läuft.
        """
        if self.running:
            current_elapsed = self.elapsed_time + (time.time() - self.start_time)
            self.timer_label.config(text=format_time(current_elapsed))
            self.update_job = self.master.after(100, self.update_timer)

    def pause_timer(self) -> None:
        """
        Pausiert den laufenden Timer und speichert die bisher verstrichene Zeit.
        """
        if self.running:
            self.running = False
            self.elapsed_time += time.time() - self.start_time
            if self.update_job:
                self.master.after_cancel(self.update_job)
                self.update_job = None
            logger.info("Timer pausiert bei %s", format_time(self.elapsed_time))

    def record_time(self) -> None:
        """
        Erfasst den aktuell laufenden Zeiteintrag und speichert ihn in der Datenbank.

        Pausiert den Timer, validiert die Eingaben, speichert den Zeiteintrag in der Datenbank und
        erstellt einen entsprechenden Redmine-Ticketeintrag, sofern eine Redmine-Verbindung besteht.
        Anschließend wird der Timer zurückgesetzt und das Backup gelöscht.
        """
        if self.running:
            self.pause_timer()
        if self.elapsed_time <= 0:
            messagebox.showwarning("Fehler", "Es wurde noch keine Zeit erfasst!")
            return
        project = self.project_combobox.get().strip()
        work_package = self.work_package_combobox.get().strip()
        if not project or not work_package:
            messagebox.showwarning("Fehler", "Projekt und Arbeitspaket müssen ausgewählt sein!")
            return
        date_str = datetime.now().strftime("%Y-%m-%d")
        try:
            self.db_manager.record_time_entry(date_str, project, work_package, self.elapsed_time)
            messagebox.showinfo("Erfolg", "Zeiterfassung gespeichert!")
        except Exception as error:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {error}")
        if hasattr(self, 'redmine_manager') and self.redmine_manager.redmine:
            self.redmine_manager.create_time_entry(
                project,
                work_package,
                self.elapsed_time,
                date_str
            )
        self.elapsed_time = 0.0
        self.timer_label.config(text="00:00:00")
        self.config_manager.clear_backup()
        self.update_forecast()

    def export_to_excel(self) -> None:
        """
        Exportiert alle Zeiteinträge in eine Excel-Datei.

        Falls keine Daten vorhanden sind, wird eine Warnmeldung angezeigt.
        """
        try:
            data = self.db_manager.fetch_all_entries()
            if not data:
                messagebox.showwarning("Fehler", "Keine Daten zum Export vorhanden.")
                return
            df = pd.DataFrame(data, columns=["Datum", "Projekt", "Arbeitspaket", "Dauer"])
            export_filename = "zeiterfassung_export.xlsx"
            df.to_excel(export_filename, index=False)
            messagebox.showinfo("Erfolg", f"Export nach {export_filename} erfolgreich!")
        except Exception as error:
            messagebox.showerror("Fehler", f"Export fehlgeschlagen: {error}")

    def show_plot_options(self) -> None:
        """
        Zeigt einen Dialog zur Auswahl von Diagrammoptionen an.

        Ermöglicht dem Benutzer die Auswahl zwischen der Darstellung der durchschnittlichen Dauer oder der Häufigkeit
        der Arbeitspakete und ruft das entsprechende Plot-Tool auf.
        """
        options_win = tk.Toplevel(self.master)
        options_win.title("Plot Optionen")
        tk.Label(options_win, text="Wählen Sie den Diagrammtyp:").grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        diagram_var = tk.StringVar(value="duration")
        rb_duration = tk.Radiobutton(options_win, text="Durchschnittliche Dauer", variable=diagram_var, value="duration",
                                     command=lambda: self.toggle_plot_options(options_win, diagram_var.get()))
        rb_frequency = tk.Radiobutton(options_win, text="Häufigkeit der Arbeitspakete", variable=diagram_var, value="frequency",
                                      command=lambda: self.toggle_plot_options(options_win, diagram_var.get()))
        rb_duration.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        rb_frequency.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.plot_options_frame = tk.Frame(options_win)
        self.plot_options_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        self.build_duration_options(self.plot_options_frame)

        def do_plot() -> None:
            selected_type = diagram_var.get()
            selected_indices = self.plot_work_package_listbox.curselection()
            selected_work_packages = [self.plot_work_package_listbox.get(i) for i in selected_indices] if selected_indices else None
            options_win.destroy()
            if selected_type == "duration":
                unit = self.unit_var.get()
                try:
                    self.plot_manager.plot_average_duration(unit=unit, selected_work_packages=selected_work_packages)
                except Exception as error:
                    messagebox.showerror("Fehler", f"Plot fehlgeschlagen: {error}")
            else:
                try:
                    self.plot_manager.plot_work_package_frequency(selected_work_packages=selected_work_packages)
                except Exception as error:
                    messagebox.showerror("Fehler", f"Plot fehlgeschlagen: {error}")

        tk.Button(options_win, text="Plot anzeigen", command=do_plot).grid(row=3, column=0, columnspan=2, pady=10)

    def toggle_plot_options(self, parent: tk.Toplevel, selected_type: str) -> None:
        """
        Wechselt zwischen den Plotoptionen basierend auf dem ausgewählten Diagrammtyp.

        Args:
            parent (tk.Toplevel): Das Optionsfenster.
            selected_type (str): Der ausgewählte Diagrammtyp.
        """
        for widget in self.plot_options_frame.winfo_children():
            widget.destroy()
        if selected_type == "duration":
            self.build_duration_options(self.plot_options_frame)
        else:
            self.build_frequency_options(self.plot_options_frame)

    def build_duration_options(self, frame: tk.Frame) -> None:
        """
        Baut die Optionen für das Diagramm der durchschnittlichen Dauer auf.

        Ermöglicht die Auswahl der Zeiteinheit und der Arbeitspakete.
        """
        tk.Label(frame, text="Wählen Sie die Einheit:").grid(row=0, column=0, sticky="w")
        self.unit_var = tk.StringVar(value="Sekunden")
        units = ["Sekunden", "Minuten", "Stunden"]
        unit_combobox = ttk.Combobox(frame, values=units, textvariable=self.unit_var, state="readonly", width=15)
        unit_combobox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        tk.Label(frame, text="Wählen Sie die Arbeitspakete:").grid(row=1, column=0, columnspan=2, sticky="w")
        self.plot_work_package_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=40, height=6)
        self.plot_work_package_listbox.grid(row=2, column=0, columnspan=2, pady=5)
        wp_dict = self.config_manager.get_work_packages()
        proj = self.project_combobox.get().strip()
        wp_list = wp_dict.get(proj, [])
        for wp in wp_list:
            self.plot_work_package_listbox.insert(tk.END, wp)

    def build_frequency_options(self, frame: tk.Frame) -> None:
        """
        Baut die Optionen für das Diagramm der Arbeitspaket-Häufigkeit auf.

        Ermöglicht die Auswahl der Arbeitspakete.
        """
        tk.Label(frame, text="Wählen Sie die Arbeitspakete:").grid(row=0, column=0, columnspan=2, sticky="w")
        self.plot_work_package_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=40, height=6)
        self.plot_work_package_listbox.grid(row=1, column=0, columnspan=2, pady=5)
        wp_dict = self.config_manager.get_work_packages()
        proj = self.project_combobox.get().strip()
        wp_list = wp_dict.get(proj, [])
        for wp in wp_list:
            self.plot_work_package_listbox.insert(tk.END, wp)

    def show_today_data(self) -> None:
        """
        Zeigt die Zeiteinträge des aktuellen Tages in einem neuen Fenster an.
        """
        today_str = date.today().strftime("%Y-%m-%d")
        entries = self.db_manager.fetch_entries_for_day(today_str)
        if not entries:
            messagebox.showinfo("Heute", "Für heute sind keine Daten vorhanden.")
            return
        win = tk.Toplevel(self.master)
        win.title(f"Daten von heute ({today_str})")
        tree = ttk.Treeview(win, columns=("Datum", "Projekt", "Arbeitspaket", "Dauer"), show="headings")
        tree.heading("Datum", text="Datum")
        tree.heading("Projekt", text="Projekt")
        tree.heading("Arbeitspaket", text="Arbeitspaket")
        tree.heading("Dauer", text="Dauer (Stunden)")
        tree.column("Datum", width=150)
        tree.column("Projekt", width=150)
        tree.column("Arbeitspaket", width=150)
        tree.column("Dauer", width=80)
        for row in entries:
            duration_seconds = row[3]
            hours = duration_seconds / 3600
            rounded_hours = math.ceil(hours * 4) / 4
            new_row = (row[0], row[1], row[2], rounded_hours)
            tree.insert("", tk.END, values=new_row)
        tree.pack(fill=tk.BOTH, expand=True)

    def auto_backup(self) -> None:
        """
        Führt ein automatisches Backup der aktuellen Timer-Daten durch.

        Speichert die verstrichene Zeit, das ausgewählte Projekt, Arbeitspaket und einen Zeitstempel in der Konfiguration.
        """
        if self.elapsed_time > 0:
            current_elapsed = self.elapsed_time + (time.time() - self.start_time) if self.running else self.elapsed_time
            backup_data = {
                "elapsed_time": current_elapsed,
                "project": self.project_combobox.get(),
                "work_package": self.work_package_combobox.get(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.config_manager.update_backup(backup_data)
        self.master.after(1000, self.auto_backup)

    def check_for_backup(self) -> None:
        """
        Prüft, ob ein ungesichertes Backup vorhanden ist, und bietet dem Benutzer Optionen zum Fortsetzen, Speichern oder Löschen.
        """
        backup = self.config_manager.get_backup()
        if backup and backup.get("elapsed_time", 0) > 0:
            dialog = BackupChoiceDialog(self.master, "Ungesicherter Timer gefunden. Fortsetzen, Speichern oder Löschen?")
            choice = dialog.result
            if choice == "fortsetzen":
                self.elapsed_time = backup["elapsed_time"]
                self.timer_label.config(text=format_time(self.elapsed_time))
                self.project_combobox.set(backup.get("project", ""))
                self.work_package_combobox.set(backup.get("work_package", ""))
            elif choice == "speichern":
                self.elapsed_time = backup["elapsed_time"]
                self.timer_label.config(text=format_time(self.elapsed_time))
                self.project_combobox.set(backup.get("project", ""))
                self.work_package_combobox.set(backup.get("work_package", ""))
                self.record_time()
            elif choice == "löschen":
                self.config_manager.clear_backup()

    def manage_projects(self) -> None:
        """
        Öffnet einen Dialog zum Verwalten der Projekte.

        Ermöglicht das Hinzufügen und Entfernen von Projekten in der Konfiguration.
        """
        win = tk.Toplevel(self.master)
        win.title("Projekte verwalten")
        tk.Label(win, text="Vorhandene Projekte:").pack(padx=10, pady=5)
        listbox = tk.Listbox(win, height=6, width=40)
        listbox.pack(padx=10, pady=5)
        projects = self.config_manager.config.get("projects", [])
        for proj in projects:
            listbox.insert(tk.END, proj)
        entry = tk.Entry(win, width=30)
        entry.pack(padx=10, pady=5)

        def add_project() -> None:
            proj = entry.get().strip()
            if proj and proj not in projects:
                projects.append(proj)
                self.config_manager.update_projects(projects)
                listbox.insert(tk.END, proj)
                self.project_combobox['values'] = projects
                entry.delete(0, tk.END)

        tk.Button(win, text="Hinzufügen", command=add_project).pack(padx=10, pady=5)

        def remove_project() -> None:
            selection = listbox.curselection()
            if selection:
                proj = listbox.get(selection[0])
                projects.remove(proj)
                self.config_manager.update_projects(projects)
                listbox.delete(selection[0])
                self.project_combobox['values'] = projects

        tk.Button(win, text="Entfernen", command=remove_project).pack(padx=10, pady=5)

    def manage_work_packages(self) -> None:
        """
        Öffnet einen Dialog zum Verwalten der Arbeitspakete (Tickets) für ein ausgewähltes Projekt.

        Ermöglicht das Hinzufügen und Entfernen von Tickets.
        """
        win = tk.Toplevel(self.master)
        win.title("Arbeitspakete verwalten")
        tk.Label(win, text="Projekt auswählen:").pack(padx=10, pady=5)
        project_var = tk.StringVar()
        project_cb = ttk.Combobox(win, values=self.config_manager.config.get("projects", []), textvariable=project_var, state="readonly")
        project_cb.pack(padx=10, pady=5)
        listbox = tk.Listbox(win, height=6, width=50)
        listbox.pack(padx=10, pady=5)

        def update_listbox(event=None) -> None:
            proj = project_var.get()
            wp_dict = self.config_manager.get_work_packages()
            tickets = wp_dict.get(proj, [])
            listbox.delete(0, tk.END)
            for t in tickets:
                listbox.insert(tk.END, t)

        project_cb.bind("<<ComboboxSelected>>", update_listbox)
        if self.config_manager.config.get("projects", []):
            project_cb.set(self.config_manager.config.get("projects", [])[0])
            update_listbox()
        tk.Label(win, text="Neues Ticket (Format: Nummer: Betreff):").pack(padx=10, pady=5)
        entry = tk.Entry(win, width=50)
        entry.pack(padx=10, pady=5)

        def add_ticket() -> None:
            proj = project_var.get()
            new_ticket = entry.get().strip()
            if new_ticket:
                wp_dict = self.config_manager.get_work_packages()
                tickets = set(wp_dict.get(proj, []))
                if new_ticket not in tickets:
                    tickets.add(new_ticket)
                    wp_dict[proj] = list(tickets)
                    self.config_manager.update_work_packages(wp_dict)
                    update_listbox()
                    entry.delete(0, tk.END)

        tk.Button(win, text="Hinzufügen", command=add_ticket).pack(padx=10, pady=5)

        def remove_ticket() -> None:
            proj = project_var.get()
            selection = listbox.curselection()
            if selection:
                wp_dict = self.config_manager.get_work_packages()
                tickets = set(wp_dict.get(proj, []))
                ticket_to_remove = listbox.get(selection[0])
                if ticket_to_remove in tickets:
                    tickets.remove(ticket_to_remove)
                    wp_dict[proj] = list(tickets)
                    self.config_manager.update_work_packages(wp_dict)
                    update_listbox()

        tk.Button(win, text="Entfernen", command=remove_ticket).pack(padx=10, pady=5)

    def on_close(self) -> None:
        """
        Behandelt das Schließen der Anwendung.

        Wenn der Timer läuft oder ungesicherte Daten vorhanden sind, wird der Benutzer gefragt, ob er die Daten
        speichern, verwerfen oder das Schließen abbrechen möchte.
        """
        if self.running or self.elapsed_time > 0:
            dialog = ClosePromptDialog(self.master, "Der Timer läuft bzw. es liegt ein Zwischenstand vor. Speichern, Verwerfen oder Abbrechen?")
            if dialog.result == "speichern":
                self.record_time()
                self.master.destroy()
            elif dialog.result == "verwerfen":
                self.config_manager.clear_backup()
                self.master.destroy()
            else:
                return
        else:
            self.master.destroy()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()
