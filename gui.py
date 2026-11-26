#!/usr/bin/env python3
"""Local control panel for the low-interaction HTTP honeypot."""

import json
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk


BG = "#0b1220"
PANEL = "#121d2e"
TEXT = "#edf4ff"
MUTED = "#9bacbf"
ACCENT = "#45d6c5"


class HoneypotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiny HTTP Honeypot")
        self.geometry("900x660")
        self.minsize(720, 540)
        self.configure(bg=BG)
        self.process = None
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="8080")
        self.title_text = tk.StringVar(value="Northstar Operations Portal")
        self._style()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Arial", 10))
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Card.TLabel", background=PANEL, foreground=TEXT)
        style.configure("TEntry", fieldbackground="#0f1928", foreground=TEXT,
                        insertcolor=TEXT, bordercolor="#31445b")
        style.configure("TButton", padding=(12, 8), background="#24364b",
                        foreground=TEXT, borderwidth=0)
        style.configure("Accent.TButton", background=ACCENT, foreground="#07131b",
                        font=("Arial", 10, "bold"))

    def _build(self):
        shell = ttk.Frame(self, padding=24)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="DEFENSIVE LAB  /  LOW INTERACTION", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(shell, text="Tiny HTTP Honeypot", font=("Arial", 25, "bold")).pack(anchor="w", pady=(6, 4))
        ttk.Label(shell, text="A fictional web decoy that records request metadata and discards form contents.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 16))
        card = ttk.Frame(shell, style="Card.TFrame", padding=16)
        card.pack(fill="x")
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x")
        fields = (("Bind address", self.host, 20), ("Port", self.port, 8),
                  ("Fictional portal title", self.title_text, 30))
        for label, variable, width in fields:
            block = ttk.Frame(row, style="Card.TFrame")
            block.pack(side="left", padx=(0, 12))
            ttk.Label(block, text=label, style="Card.TLabel").pack(anchor="w", pady=(0, 6))
            ttk.Entry(block, textvariable=variable, width=width).pack()
        controls = ttk.Frame(card, style="Card.TFrame")
        controls.pack(fill="x", pady=(14, 0))
        self.start_button = ttk.Button(controls, text="Start local decoy", style="Accent.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))
        self.status = tk.StringVar(value="Safe default: only this computer can connect.")
        ttk.Label(shell, textvariable=self.status, style="Muted.TLabel").pack(anchor="w", pady=(16, 8))
        self.log = tk.Text(shell, bg="#070d16", fg=TEXT, insertbackground=TEXT,
                           relief="flat", padx=16, pady=14, font=("Menlo", 10), wrap="word")
        self.log.pack(fill="both", expand=True)
        self.log.insert("end", "Request events will appear here. Form values are not collected.\n")
        self.log.configure(state="disabled")
        notice = "Use only an isolated or authorised network. Do not enter real credentials or imitate a real company."
        ttk.Label(shell, text=notice, style="Muted.TLabel").pack(anchor="w", pady=(8, 0))

    def start(self):
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            self.status.set("Port must be a number from 1 to 65535.")
            return
        host = self.host.get().strip()
        title = self.title_text.get().strip()
        if not host or not title:
            self.status.set("Enter a bind address and fictional title.")
            return
        self.process = subprocess.Popen(
            [sys.executable, "honeypot.py", "--host", host, "--port", str(port), "--title", title],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.set(f"Starting on {host}:{port}…")
        threading.Thread(target=self.read_events, daemon=True).start()

    def read_events(self):
        process = self.process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            self.after(0, self.append_event, line.rstrip())
        self.after(0, self.stopped)

    def append_event(self, line):
        try:
            item = json.loads(line)
            if item.get("event") == "http_request":
                line = (f'{item.get("time")}  {item.get("source_ip")}:{item.get("source_port")}  '
                        f'{item.get("method")} {item.get("path")}  ({item.get("body_bytes")} body bytes)')
        except json.JSONDecodeError:
            pass
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        if '"event": "listening"' in line:
            self.status.set("Listening. Use the local URL shown by your browser.")

    def stopped(self):
        self.process = None
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status.set("Decoy stopped.")

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.stopped()

    def close(self):
        self.stop()
        self.destroy()


if __name__ == "__main__":
    HoneypotApp().mainloop()
