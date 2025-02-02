"""
@file dialogs.py
@brief Wiederverwendbare Dialogklassen für die Zeiterfassung.
@version CHOE 02.02.2025
@details Diese Datei enthält Dialoge zur Auswahl von Backup-Optionen sowie zum Bestätigen des Programmendes.
"""

import tkinter as tk

class BackupChoiceDialog(tk.Toplevel):
    """
    @brief Dialog zur Auswahl einer Backup-Option.
    @details Ermöglicht dem Benutzer, einen ungesicherten Timer fortzusetzen, zu speichern oder zu löschen.
    """
    def __init__(self, parent, message):
        super().__init__(parent)
        self.title("Ungesicherter Timer gefunden")
        self.result = None
        tk.Label(self, text=message, padx=20, pady=10).pack()
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Fortsetzen", command=self.choose_resume).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Speichern", command=self.choose_save).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Löschen", command=self.choose_delete).pack(side=tk.LEFT, padx=5)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def choose_resume(self):
        """
        @brief Setzt die Auswahl auf 'fortsetzen' und schließt den Dialog.
        """
        self.result = "fortsetzen"
        self.destroy()

    def choose_save(self):
        """
        @brief Setzt die Auswahl auf 'speichern' und schließt den Dialog.
        """
        self.result = "speichern"
        self.destroy()

    def choose_delete(self):
        """
        @brief Setzt die Auswahl auf 'löschen' und schließt den Dialog.
        """
        self.result = "löschen"
        self.destroy()

    def on_close(self):
        """
        @brief Wird aufgerufen, wenn der Dialog geschlossen wird.
        """
        self.result = None
        self.destroy()

class ClosePromptDialog(tk.Toplevel):
    """
    @brief Dialog, der beim Schließen der Anwendung erscheint, wenn der Timer läuft.
    @details Ermöglicht dem Benutzer, den Timer zu speichern, zu verwerfen oder das Schließen abzubrechen.
    """
    def __init__(self, parent, message):
        super().__init__(parent)
        self.title("Timer läuft noch")
        self.result = None
        tk.Label(self, text=message, padx=20, pady=10).pack()
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Speichern", command=self.choose_save).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Verwerfen", command=self.choose_discard).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Abbrechen", command=self.choose_cancel).pack(side=tk.LEFT, padx=5)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def choose_save(self):
        """
        @brief Setzt die Auswahl auf 'speichern' und schließt den Dialog.
        """
        self.result = "speichern"
        self.destroy()

    def choose_discard(self):
        """
        @brief Setzt die Auswahl auf 'verwerfen' und schließt den Dialog.
        """
        self.result = "verwerfen"
        self.destroy()

    def choose_cancel(self):
        """
        @brief Setzt die Auswahl auf 'abbrechen' und schließt den Dialog.
        """
        self.result = "abbrechen"
        self.destroy()

    def on_close(self):
        """
        @brief Wird aufgerufen, wenn der Dialog geschlossen wird.
        """
        self.result = "abbrechen"
        self.destroy()
