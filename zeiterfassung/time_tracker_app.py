"""
@file time_tracker_app.py
@brief Hauptanwendung der Zeiterfassung.
@version CHOE 02.02.2025
@details Diese Datei integriert alle Module (Konfiguration, Datenbank, Plot, Dialoge) und bietet die Benutzeroberfläche inklusive Timer, Prognoseanzeige, Export, Plot und Anzeige der heutigen Daten.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
from datetime import datetime, date
import pandas as pd
import logging
import math

from config_manager import ConfigManager
from database_manager import DatabaseManager
from plot_manager import PlotManager
from dialogs import BackupChoiceDialog, ClosePromptDialog

logger = logging.getLogger(__name__)

def format_time(seconds):
    """
    @brief Formatiert eine Zeitangabe in Sekunden in das Format HH:MM:SS.
    @param seconds Zeit in Sekunden.
    @return Zeit als String im Format HH:MM:SS.
    """
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

class TimeTrackerApp:
    """
    @brief Hauptklasse der Zeiterfassungsanwendung.
    @details Diese Klasse stellt die grafische Benutzeroberfläche bereit und integriert alle Funktionalitäten (Timer, Prognoseanzeige, Export, Plot, Tagesdatenanzeige).
    """
    def __init__(self, master):
        """
        @brief Initialisiert die Anwendung.
        @param master Das Hauptfenster.
        """
        self.master = master
        self.master.title("Zeiterfassung")
        logger.info("Zeiterfassung gestartet.")
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.plot_manager = PlotManager(self.db_manager)
        self.elapsed_time = 0.0
        self.running = False
        self.start_time = None
        self.update_job = None
        self.create_widgets()
        self.check_for_backup()
        self.auto_backup()
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """
        @brief Erstellt und platziert alle GUI-Elemente.
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
        self.project_combobox = ttk.Combobox(self.master, values=self.config_manager.get_projects(), state="readonly", width=27)
        self.project_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        if self.config_manager.get_projects():
            self.project_combobox.set(self.config_manager.get_projects()[0])
        self.project_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_forecast())
        tk.Button(self.master, text="Verwalten", command=self.manage_projects).grid(row=2, column=2, padx=5, pady=5)
        tk.Label(self.master, text="Arbeitspaket:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.work_package_combobox = ttk.Combobox(self.master, values=self.config_manager.get_work_packages(), state="readonly", width=27)
        self.work_package_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        if self.config_manager.get_work_packages():
            self.work_package_combobox.set(self.config_manager.get_work_packages()[0])
        self.work_package_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_forecast())
        tk.Button(self.master, text="Verwalten", command=self.manage_work_packages).grid(row=3, column=2, padx=5, pady=5)
        self.export_button = tk.Button(self.master, text="Export nach Excel", command=self.export_to_excel)
        self.export_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.plot_button = tk.Button(self.master, text="Plot anzeigen", command=self.show_plot_options)
        self.plot_button.grid(row=4, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
        self.today_button = tk.Button(self.master, text="Heute anzeigen", command=self.show_today_data)
        self.today_button.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        self.update_forecast()

    def update_forecast(self):
        """
        @brief Aktualisiert die Prognoseanzeige basierend auf den historischen Einträgen.
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

    def start_timer(self):
        """
        @brief Startet den Timer.
        """
        if not self.running:
            self.running = True
            self.start_time = time.time()
            logger.info("Timer gestartet.")
            self.update_timer()

    def update_timer(self):
        """
        @brief Aktualisiert die Timeranzeige.
        """
        if self.running:
            current_elapsed = self.elapsed_time + (time.time() - self.start_time)
            self.timer_label.config(text=format_time(current_elapsed))
            self.update_job = self.master.after(100, self.update_timer)

    def pause_timer(self):
        """
        @brief Pausiert den Timer.
        """
        if self.running:
            self.running = False
            self.elapsed_time += time.time() - self.start_time
            if self.update_job:
                self.master.after_cancel(self.update_job)
                self.update_job = None
            logger.info("Timer pausiert bei %s", format_time(self.elapsed_time))

    def record_time(self):
        """
        @brief Speichert den aktuellen Zeiteintrag.
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
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.db_manager.record_time_entry(date_str, project, work_package, self.elapsed_time)
            messagebox.showinfo("Erfolg", "Zeiterfassung gespeichert!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
        self.elapsed_time = 0.0
        self.timer_label.config(text="00:00:00")
        self.config_manager.clear_backup()
        self.update_forecast()

    def export_to_excel(self):
        """
        @brief Exportiert alle Zeiteinträge in eine Excel-Datei.
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
        except Exception as e:
            messagebox.showerror("Fehler", f"Export fehlgeschlagen: {e}")

    def show_plot_options(self):
        """
        @brief Zeigt ein Optionsfenster zur Auswahl der Plot-Parameter.
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
        def do_plot():
            selected_type = diagram_var.get()
            selected_indices = self.plot_work_package_listbox.curselection()
            selected_work_packages = [self.plot_work_package_listbox.get(i) for i in selected_indices]
            if not selected_work_packages:
                selected_work_packages = None
            options_win.destroy()
            if selected_type == "duration":
                unit = self.unit_var.get()
                try:
                    self.plot_manager.plot_average_duration(unit=unit, selected_work_packages=selected_work_packages)
                except Exception as e:
                    messagebox.showerror("Fehler", f"Plot fehlgeschlagen: {e}")
            else:
                try:
                    self.plot_manager.plot_work_package_frequency(selected_work_packages=selected_work_packages)
                except Exception as e:
                    messagebox.showerror("Fehler", f"Plot fehlgeschlagen: {e}")
        tk.Button(options_win, text="Plot anzeigen", command=do_plot).grid(row=3, column=0, columnspan=2, pady=10)

    def toggle_plot_options(self, parent, selected_type):
        """
        @brief Aktualisiert die zusätzlichen Optionen im Plot-Optionsfenster.
        @param selected_type Gewählter Diagrammtyp.
        """
        for widget in self.plot_options_frame.winfo_children():
            widget.destroy()
        if selected_type == "duration":
            self.build_duration_options(self.plot_options_frame)
        else:
            self.build_frequency_options(self.plot_options_frame)

    def build_duration_options(self, frame):
        """
        @brief Baut die Optionen für das Diagramm 'Durchschnittliche Dauer'.
        @param frame Der Container, in dem die Optionen angezeigt werden.
        """
        tk.Label(frame, text="Wählen Sie die Einheit:").grid(row=0, column=0, sticky="w")
        self.unit_var = tk.StringVar(value="Sekunden")
        units = ["Sekunden", "Minuten", "Stunden"]
        unit_combobox = ttk.Combobox(frame, values=units, textvariable=self.unit_var, state="readonly", width=15)
        unit_combobox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        tk.Label(frame, text="Wählen Sie die Arbeitspakete, die einbezogen werden sollen:").grid(row=1, column=0, columnspan=2, sticky="w")
        self.plot_work_package_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=40, height=6)
        self.plot_work_package_listbox.grid(row=2, column=0, columnspan=2, pady=5)
        for wp in self.config_manager.get_work_packages():
            self.plot_work_package_listbox.insert(tk.END, wp)

    def build_frequency_options(self, frame):
        """
        @brief Baut die Optionen für das Diagramm 'Häufigkeit der Arbeitspakete'.
        @param frame Der Container, in dem die Optionen angezeigt werden.
        """
        tk.Label(frame, text="Wählen Sie die Arbeitspakete, die einbezogen werden sollen:").grid(row=0, column=0, columnspan=2, sticky="w")
        self.plot_work_package_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=40, height=6)
        self.plot_work_package_listbox.grid(row=1, column=0, columnspan=2, pady=5)
        for wp in self.config_manager.get_work_packages():
            self.plot_work_package_listbox.insert(tk.END, wp)

    def show_today_data(self):
        """
        @brief Zeigt alle Zeiteinträge des heutigen Tages in einem neuen Fenster an.
        @details Die Dauer wird in Stunden angezeigt und auf 0,25er-Schritte aufgerundet.
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

    def auto_backup(self):
        """
        @brief Führt ein automatisches Backup des aktuellen Timer-Zwischenstands durch.
        """
        if self.elapsed_time > 0:
            if self.running:
                current_elapsed = self.elapsed_time + (time.time() - self.start_time)
            else:
                current_elapsed = self.elapsed_time
            backup_data = {
                "elapsed_time": current_elapsed,
                "project": self.project_combobox.get(),
                "work_package": self.work_package_combobox.get(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.config_manager.update_backup(backup_data)
        self.master.after(1000, self.auto_backup)

    def check_for_backup(self):
        """
        @brief Überprüft, ob ein ungesicherter Timer-Zwischenstand vorhanden ist, und fragt den Benutzer.
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

    def manage_projects(self):
        """
        @brief Öffnet ein Fenster zur Verwaltung der Projekte.
        """
        win = tk.Toplevel(self.master)
        win.title("Projekte verwalten")
        tk.Label(win, text="Vorhandene Projekte:").pack(padx=10, pady=5)
        listbox = tk.Listbox(win, height=6, width=40)
        listbox.pack(padx=10, pady=5)
        projects = self.config_manager.get_projects()
        for proj in projects:
            listbox.insert(tk.END, proj)
        entry = tk.Entry(win, width=30)
        entry.pack(padx=10, pady=5)
        def add_project():
            proj = entry.get().strip()
            if proj and proj not in projects:
                projects.append(proj)
                self.config_manager.update_projects(projects)
                listbox.insert(tk.END, proj)
                self.project_combobox['values'] = projects
                entry.delete(0, tk.END)
        tk.Button(win, text="Hinzufügen", command=add_project).pack(padx=10, pady=5)
        def remove_project():
            selection = listbox.curselection()
            if selection:
                proj = listbox.get(selection[0])
                projects.remove(proj)
                self.config_manager.update_projects(projects)
                listbox.delete(selection[0])
                self.project_combobox['values'] = projects
        tk.Button(win, text="Entfernen", command=remove_project).pack(padx=10, pady=5)

    def manage_work_packages(self):
        """
        @brief Öffnet ein Fenster zur Verwaltung der Arbeitspakete.
        """
        win = tk.Toplevel(self.master)
        win.title("Arbeitspakete verwalten")
        tk.Label(win, text="Vorhandene Arbeitspakete:").pack(padx=10, pady=5)
        listbox = tk.Listbox(win, height=6, width=40)
        listbox.pack(padx=10, pady=5)
        work_packages = self.config_manager.get_work_packages()
        for wp in work_packages:
            listbox.insert(tk.END, wp)
        entry = tk.Entry(win, width=30)
        entry.pack(padx=10, pady=5)
        def add_work_package():
            wp = entry.get().strip()
            if wp and wp not in work_packages:
                work_packages.append(wp)
                self.config_manager.update_work_packages(work_packages)
                listbox.insert(tk.END, wp)
                self.work_package_combobox['values'] = work_packages
                entry.delete(0, tk.END)
        tk.Button(win, text="Hinzufügen", command=add_work_package).pack(padx=10, pady=5)
        def remove_work_package():
            selection = listbox.curselection()
            if selection:
                wp = listbox.get(selection[0])
                work_packages.remove(wp)
                self.config_manager.update_work_packages(work_packages)
                listbox.delete(selection[0])
                self.work_package_combobox['values'] = work_packages
        tk.Button(win, text="Entfernen", command=remove_work_package).pack(padx=10, pady=5)

    def on_close(self):
        """
        @brief Behandelt das Schließen der Anwendung.
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
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()
