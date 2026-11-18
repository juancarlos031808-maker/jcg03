import os
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


def default_database():
    """Store user data outside the downloaded source folder."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    folder = base / "TaskDesk"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "tasks.sqlite3"


class TaskStore:
    """SQLite commits keep tasks saved between sessions."""

    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY, title TEXT NOT NULL, "
            "priority TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.connection.commit()

    def get_theme(self):
        row = self.connection.execute(
            "SELECT value FROM settings WHERE key='theme'"
        ).fetchone()
        return "dark" if row and row["value"] == "dark" else "light"

    def set_theme(self, theme):
        if theme not in ("light", "dark"):
            raise ValueError("Choose light or dark mode.")
        with self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', ?)",
                (theme,),
            )

    def all(self):
        return self.connection.execute(
            "SELECT * FROM tasks ORDER BY done, "
            "CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, id DESC"
        ).fetchall()

    def save(self, title, priority, task_id=None):
        title = title.strip()
        if not title or len(title) > 160:
            raise ValueError("Enter a task between 1 and 160 characters.")
        if priority not in ("High", "Medium", "Low"):
            raise ValueError("Choose High, Medium, or Low priority.")
        with self.connection:
            if task_id is None:
                self.connection.execute(
                    "INSERT INTO tasks (title, priority) VALUES (?, ?)", (title, priority)
                )
            else:
                self.connection.execute(
                    "UPDATE tasks SET title=?, priority=? WHERE id=?",
                    (title, priority, task_id),
                )

    def toggle(self, task_id):
        with self.connection:
            self.connection.execute("UPDATE tasks SET done=1-done WHERE id=?", (task_id,))

    def delete(self, task_id):
        with self.connection:
            self.connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def close(self):
        self.connection.close()


class TaskDesk(tk.Tk):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.editing_id = None
        self.dark_mode = tk.BooleanVar(self, value=store.get_theme() == "dark")
        self.title("Task Desk | Python GUI Project")
        self.geometry("900x620")
        self.minsize(760, 520)
        self.configure(bg="#edf2f7")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.setup_style()
        self.build_interface()
        self.apply_theme()
        self.refresh()
        self.bind("<Control-n>", lambda event: self.reset_editor())
        self.bind("<Control-f>", lambda event: self.search_entry.focus_set())

    def setup_style(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TLabel", font=("Segoe UI", 11))
        self.style.configure("Title.TLabel", font=("Segoe UI", 27, "bold"))
        self.style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10))
        self.style.configure("TCheckbutton", font=("Segoe UI", 11), padding=8)
        self.style.configure("Treeview", rowheight=36, font=("Segoe UI", 11))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), padding=8)
        self.apply_theme()

    def apply_theme(self):
        """Recolor existing widgets without rebuilding the task list or editor."""
        if self.dark_mode.get():
            colors = dict(bg="#17212f", surface="#223044", fg="#edf3fc",
                          muted="#b1bfd1", border="#52647c", hover="#33465f",
                          accent="#235bd6", accent_hover="#1645ac")
        else:
            colors = dict(bg="#edf2f7", surface="#ffffff", fg="#172d43",
                          muted="#53677c", border="#a0aec0", hover="#dae4f0",
                          accent="#235bd6", accent_hover="#1645ac")
        c = colors
        style = self.style
        self.configure(background=c["bg"])
        style.configure(".", background=c["bg"], foreground=c["fg"],
                        bordercolor=c["border"], lightcolor=c["border"],
                        darkcolor=c["border"], troughcolor=c["bg"],
                        selectbackground=c["accent"], selectforeground="white")
        style.configure("TFrame", background=c["bg"])
        style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        style.configure("Sub.TLabel", foreground=c["muted"])
        style.configure("TButton", background=c["surface"], foreground=c["fg"])
        style.map("TButton", background=[("pressed", c["hover"]), ("active", c["hover"])],
                  foreground=[("disabled", c["muted"]), ("active", c["fg"])])
        style.configure("Accent.TButton", background=c["accent"], foreground="white")
        style.map("Accent.TButton", background=[("pressed", c["accent_hover"]), ("active", c["accent_hover"])],
                  foreground=[("active", "white")])
        style.configure("TCheckbutton", background=c["bg"], foreground=c["fg"],
                        indicatorbackground=c["surface"], indicatorforeground=c["fg"])
        style.map("TCheckbutton", background=[("active", c["hover"])],
                  foreground=[("active", c["fg"])],
                  indicatorbackground=[("selected", c["accent"])],
                  indicatorforeground=[("selected", "white")])
        for widget_style in ("TEntry", "TCombobox"):
            style.configure(widget_style, fieldbackground=c["surface"],
                            background=c["surface"], foreground=c["fg"],
                            insertcolor=c["fg"], arrowcolor=c["fg"])
            style.map(widget_style, fieldbackground=[("readonly", c["surface"])],
                      foreground=[("readonly", c["fg"])],
                      selectbackground=[("!disabled", c["accent"])],
                      selectforeground=[("!disabled", "white")])
        style.map("TCombobox", background=[("active", c["hover"]), ("readonly", c["surface"])],
                  arrowcolor=[("!disabled", c["fg"])])
        style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"], foreground=c["fg"])
        style.map("Treeview", background=[("selected", c["accent"])], foreground=[("selected", "white")])
        style.configure("Treeview.Heading", background=c["bg"], foreground=c["fg"])
        style.map("Treeview.Heading", background=[("active", c["hover"])])
        style.configure("Vertical.TScrollbar", background=c["surface"], arrowcolor=c["fg"])
        style.map("Vertical.TScrollbar", background=[("active", c["hover"]), ("pressed", c["hover"])])
        # Combobox menus are Tk listboxes, so ttk styles do not color them.
        for option, value in (("background", c["surface"]), ("foreground", c["fg"]),
                              ("selectBackground", c["accent"]), ("selectForeground", "white")):
            self.option_add("*TCombobox*Listbox." + option, value)
        if hasattr(self, "tree"):
            self.tree.tag_configure("completed", foreground=c["muted"])
            for combo in (self.priority_combo, self.filter_combo):
                popdown = self.tk.call("ttk::combobox::PopdownWindow", str(combo))
                self.tk.call(str(popdown) + ".f.l", "configure",
                             "-background", c["surface"], "-foreground", c["fg"],
                             "-selectbackground", c["accent"], "-selectforeground", "white")

    def toggle_theme(self):
        theme = "dark" if self.dark_mode.get() else "light"
        try:
            self.store.set_theme(theme)
        except sqlite3.Error as error:
            self.dark_mode.set(not self.dark_mode.get())
            messagebox.showerror("Could not save appearance", str(error), parent=self)
            return
        self.apply_theme()
        self.notice_var.set(f"{theme.capitalize()} mode enabled. Your choice is saved.")

    def build_interface(self):
        main = ttk.Frame(self, padding=24)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)
        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Task Desk", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(header, text="Dark mode", variable=self.dark_mode,
                        command=self.toggle_theme).grid(row=0, column=1, sticky="e")
        ttk.Label(main, text="A little structure for your next big idea.", style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 18))

        editor = ttk.Frame(main)
        editor.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        editor.columnconfigure(0, weight=1)
        ttk.Label(editor, text="Task").grid(row=0, column=0, sticky="w")
        ttk.Label(editor, text="Priority").grid(row=0, column=1, sticky="w", padx=10)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(editor, textvariable=self.title_var, font=("Segoe UI", 12))
        self.title_entry.grid(row=1, column=0, sticky="ew", ipady=7)
        self.title_entry.bind("<Return>", lambda event: self.save_task())
        self.priority_var = tk.StringVar(value="Medium")
        self.priority_combo = ttk.Combobox(editor, textvariable=self.priority_var, values=("High", "Medium", "Low"), state="readonly", width=10)
        self.priority_combo.grid(row=1, column=1, padx=10, ipady=7)
        self.save_button = ttk.Button(editor, text="Add task", style="Accent.TButton", command=self.save_task)
        self.save_button.grid(row=1, column=2)
        ttk.Button(editor, text="Clear", command=self.reset_editor).grid(row=1, column=3, padx=(8, 0))

        filters = ttk.Frame(main)
        filters.grid(row=3, column=0, sticky="ew", pady=(12, 8))
        filters.columnconfigure(1, weight=1)
        ttk.Label(filters, text="Search").grid(row=0, column=0, padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", ipady=5)
        self.filter_var = tk.StringVar(value="All tasks")
        self.filter_combo = ttk.Combobox(filters, textvariable=self.filter_var, values=("All tasks", "Active", "Completed"), state="readonly", width=14)
        self.filter_combo.grid(row=0, column=2, padx=(12, 0), ipady=5)
        self.search_var.trace_add("write", lambda *args: self.refresh())
        self.filter_var.trace_add("write", lambda *args: self.refresh())
        self.stats_var = tk.StringVar()
        ttk.Label(main, textvariable=self.stats_var, style="Sub.TLabel").grid(row=4, column=0, sticky="w", pady=(4, 10))

        table = ttk.Frame(main)
        table.grid(row=5, column=0, sticky="nsew")
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=("status", "title", "priority"), show="headings", selectmode="browse")
        for column, label, width in (("status", "Status", 110), ("title", "Task", 440), ("priority", "Priority", 100)):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, minwidth=80, stretch=column == "title")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.tag_configure("completed", foreground="#6a7b8c")
        self.tree.bind("<Double-1>", self.edit_task)

        actions = ttk.Frame(main)
        actions.grid(row=6, column=0, sticky="ew", pady=(14, 10))
        ttk.Button(actions, text="Complete / Reopen", command=self.toggle_task).pack(side="left")
        ttk.Button(actions, text="Edit", command=self.edit_task).pack(side="left", padx=8)
        ttk.Button(actions, text="Delete", command=self.delete_task).pack(side="left")
        self.notice_var = tk.StringVar(value="Tasks save automatically. Double-click a task to edit it.")
        ttk.Label(main, textvariable=self.notice_var, style="Sub.TLabel").grid(row=7, column=0, sticky="w")
        self.title_entry.focus_set()

    def refresh(self):
        selected = self.tree.selection()
        rows = self.store.all()
        completed = sum(row["done"] for row in rows)
        query = self.search_var.get().casefold().strip()
        view = self.filter_var.get()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            if query not in row["title"].casefold():
                continue
            if view == "Active" and row["done"] or view == "Completed" and not row["done"]:
                continue
            self.tree.insert("", "end", iid=str(row["id"]), values=("Done" if row["done"] else "To do", row["title"], row["priority"]), tags=("completed",) if row["done"] else ())
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])
        self.stats_var.set(f"{len(rows) - completed} active  /  {completed} completed  /  {len(self.tree.get_children())} shown")

    def selected_id(self):
        selected = self.tree.selection()
        if not selected:
            self.notice_var.set("Select a task in the list first.")
            return None
        return int(selected[0])

    def reset_editor(self):
        self.editing_id = None
        self.title_var.set("")
        self.priority_var.set("Medium")
        self.save_button.configure(text="Add task")
        self.title_entry.focus_set()

    def save_task(self):
        try:
            self.store.save(self.title_var.get(), self.priority_var.get(), self.editing_id)
        except ValueError as error:
            messagebox.showwarning("Check task", str(error), parent=self)
            return
        except sqlite3.Error as error:
            messagebox.showerror("Could not save", str(error), parent=self)
            return
        self.reset_editor()
        self.refresh()
        self.notice_var.set("Task saved. Clear search or filters if you cannot see it.")

    def edit_task(self, event=None):
        task_id = self.selected_id()
        if task_id is None:
            return
        row = next((row for row in self.store.all() if row["id"] == task_id), None)
        if row is None:
            self.refresh()
            return
        self.editing_id = task_id
        self.title_var.set(row["title"])
        self.priority_var.set(row["priority"])
        self.save_button.configure(text="Save changes")
        self.title_entry.focus_set()
        self.title_entry.selection_range(0, "end")

    def toggle_task(self):
        task_id = self.selected_id()
        if task_id is not None:
            self.store.toggle(task_id)
            self.refresh()
            self.notice_var.set("Task status saved.")

    def delete_task(self):
        task_id = self.selected_id()
        if task_id is not None and messagebox.askyesno("Delete task?", "Permanently delete the selected task?", parent=self):
            self.store.delete(task_id)
            if self.editing_id == task_id:
                self.reset_editor()
            self.refresh()
            self.notice_var.set("Task deleted.")

    def report_callback_exception(self, exception, value, traceback):
        messagebox.showerror("Task Desk error", str(value), parent=self)

    def close(self):
        self.store.close()
        self.destroy()


def main():
    store = TaskStore(default_database())
    try:
        app = TaskDesk(store)
        app.mainloop()
    finally:
        store.close()


if __name__ == "__main__":
    main()
