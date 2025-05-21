import time
import pygame
import pyttsx3
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# Initialize the speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)
engine.setProperty('voice', voices[0].id)

# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Initialize pygame mixer
pygame.mixer.init()

ALARM_FILE = "alarms.txt"

def play_alarm_sound(alarm_task, alarm_time):
    try:
        speak(f"Alarm! Time to {alarm_task} at {alarm_time}")
        messagebox.showinfo("Alarm!", f"Time to {alarm_task} at {alarm_time}")
    except Exception as e:
        print(f"Error in alarm sound: {e}")

def load_alarms():
    alarms = []
    if os.path.exists(ALARM_FILE):
        try:
            with open(ALARM_FILE, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    parts = line.strip().split(" | ")
                    if len(parts) == 3:
                        alarm_time, alarm_task, status = parts
                        alarms.append((alarm_time, alarm_task, status))
        except Exception as e:
            speak("Error loading alarms from file")
    return alarms

def save_alarm(alarm_time, alarm_task, status="not proceeded"):
    try:
        with open(ALARM_FILE, 'a') as file:
            file.write(f"{alarm_time} | {alarm_task} | {status}\n")
    except Exception as e:
        speak("Error saving alarm to file")

def save_all_alarms(alarms):
    try:
        with open(ALARM_FILE, 'w') as file:
            for alarm_time, alarm_task, status in alarms:
                file.write(f"{alarm_time} | {alarm_task} | {status}\n")
    except Exception as e:
        speak("Error saving all alarms to file")

def all_alarms_past(alarms):
    current_time = time.strftime("%H:%M")
    for alarm_time, _, _ in alarms:
        if alarm_time >= current_time:
            return False
    return True

class AlarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alarm Manager")
        self.root.geometry("700x450")
        self.root.resizable(False, False)

        self.alarms = load_alarms()
        self.checking = False

        # Treeview
        self.tree = ttk.Treeview(root, columns=("Time", "Task", "Status"), show="headings")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Task", text="Task")
        self.tree.heading("Status", text="Status")
        self.tree.column("Time", width=100)
        self.tree.column("Task", width=300)
        self.tree.column("Status", width=150)
        self.tree.pack(pady=10, fill="both", expand=True)

        # Button Frame
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Set Alarm", width=12, command=self.set_alarm).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Edit Alarm", width=12, command=self.edit_alarm).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Alarm", width=12, command=self.delete_alarm).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Refresh", width=12, command=self.refresh).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Start Checking", width=14, command=self.start_checking).grid(row=0, column=4, padx=5)
        tk.Button(btn_frame, text="Close", width=12, command=self.root.quit).grid(row=0, column=5, padx=5)

        # Status Label
        self.check_label = tk.Label(root, text="", font=("Helvetica", 10), fg="blue")
        self.check_label.pack(pady=5)

        self.refresh()

    def refresh(self):
        self.alarms = load_alarms()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for alarm_time, alarm_task, status in self.alarms:
            symbol = "✅" if status == "proceeded" else "⏳"
            self.tree.insert("", "end", values=(alarm_time, alarm_task, f"{symbol} {status}"))

    def set_alarm(self):
        alarm_time = simpledialog.askstring("Alarm Time", "Enter time (HH:MM):")
        if not alarm_time:
            return
        alarm_task = simpledialog.askstring("Alarm Task", "Enter task:")
        if not alarm_task:
            return
        save_alarm(alarm_time, alarm_task)
        self.alarms.append((alarm_time, alarm_task, "not proceeded"))
        speak(f"Alarm set with task {alarm_task}.")
        self.refresh()

    def edit_alarm(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Edit Alarm", "No alarm selected.")
            return
        index = self.tree.index(selected[0])
        alarm_time, alarm_task, status = self.alarms[index]
        new_time = simpledialog.askstring("New Time", f"Enter new time or leave blank to keep ({alarm_time}):")
        new_task = simpledialog.askstring("New Task", f"Enter new task or leave blank to keep ({alarm_task}):")

        if new_time:
            alarm_time = new_time
        if new_task:
            alarm_task = new_task

        self.alarms[index] = (alarm_time, alarm_task, status)
        save_all_alarms(self.alarms)
        speak(f"Alarm updated: Task {alarm_task}")
        self.refresh()

    def delete_alarm(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Delete Alarm", "No alarm selected.")
            return
        index = self.tree.index(selected[0])
        alarm_time, alarm_task, _ = self.alarms[index]
        confirm = messagebox.askyesno("Delete Alarm", f"Delete alarm: {alarm_time} - {alarm_task}?")
        if confirm:
            del self.alarms[index]
            save_all_alarms(self.alarms)
            speak(f"Deleted alarm ")
            self.refresh()

    def start_checking(self):
        if self.checking:
            return
        self.checking = True
        speak("Starting alarm check.")
        self.check_label.config(text="⏱ Checking for alarms...")
        self.check_alarms()

    def check_alarms(self):
        if all_alarms_past(self.alarms):
            speak("All alarms have passed. Stopping.")
            self.check_label.config(text="✅ All alarms completed.")
            return

        current_time = time.strftime("%H:%M")
        for i, (alarm_time, alarm_task, status) in enumerate(self.alarms):
            if current_time == alarm_time and status == "not proceeded":
                play_alarm_sound(alarm_task, alarm_time)
                self.alarms[i] = (alarm_time, alarm_task, "proceeded")
                save_all_alarms(self.alarms)
                self.refresh()
                break

        if self.checking:
            self.root.after(1000, self.check_alarms)

if __name__ == "__main__":
    root = tk.Tk()
    app = AlarmApp(root)
    root.mainloop()
