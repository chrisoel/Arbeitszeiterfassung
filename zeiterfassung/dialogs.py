#!/usr/bin/env python
"""
dialogs.py
----------
Wiederverwendbare Dialogklassen für die Zeiterfassung.

Dieses Modul enthält Dialoge zur Auswahl von Backup-Optionen sowie zum Bestätigen des Programmendes.

Version: CHOE 10.02.2025
"""

import tkinter as tk


class BackupChoiceDialog(tk.Toplevel):
    """
    Dialog zur Auswahl der Backup-Optionen.

    Dieser Dialog informiert den Benutzer darüber, dass ein ungesicherter Timer gefunden wurde,
    und bietet die Optionen an, den Timer fortzusetzen, zu speichern oder zu löschen.
    """

    def __init__(self, parent, message: str) -> None:
        """
        Initialisiert den BackupChoiceDialog.

        Args:
            parent: Das übergeordnete Tkinter-Fenster.
            message (str): Die anzuzeigende Nachricht im Dialog.
        """
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

    def choose_resume(self) -> None:
        """
        Setzt das Ergebnis auf "fortsetzen" und schließt den Dialog.
        """
        self.result = "fortsetzen"
        self.destroy()

    def choose_save(self) -> None:
        """
        Setzt das Ergebnis auf "speichern" und schließt den Dialog.
        """
        self.result = "speichern"
        self.destroy()

    def choose_delete(self) -> None:
        """
        Setzt das Ergebnis auf "löschen" und schließt den Dialog.
        """
        self.result = "löschen"
        self.destroy()

    def on_close(self) -> None:
        """
        Behandelt das Schließen des Dialogs durch den Benutzer.

        Setzt das Ergebnis auf None und schließt den Dialog.
        """
        self.result = None
        self.destroy()


class ClosePromptDialog(tk.Toplevel):
    """
    Dialog zur Bestätigung des Programmendes bei laufendem Timer.

    Dieser Dialog weist darauf hin, dass der Timer noch läuft, und bietet die Optionen,
    den Timer zu speichern, zu verwerfen oder das Schließen abzubrechen.
    """

    def __init__(self, parent, message: str) -> None:
        """
        Initialisiert den ClosePromptDialog.

        Args:
            parent: Das übergeordnete Tkinter-Fenster.
            message (str): Die anzuzeigende Nachricht im Dialog.
        """
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

    def choose_save(self) -> None:
        """
        Setzt das Ergebnis auf "speichern" und schließt den Dialog.
        """
        self.result = "speichern"
        self.destroy()

    def choose_discard(self) -> None:
        """
        Setzt das Ergebnis auf "verwerfen" und schließt den Dialog.
        """
        self.result = "verwerfen"
        self.destroy()

    def choose_cancel(self) -> None:
        """
        Setzt das Ergebnis auf "abbrechen" und schließt den Dialog.
        """
        self.result = "abbrechen"
        self.destroy()

    def on_close(self) -> None:
        """
        Behandelt das Schließen des Dialogs durch den Benutzer.

        Setzt das Ergebnis auf "abbrechen" und schließt den Dialog.
        """
        self.result = "abbrechen"
        self.destroy()
