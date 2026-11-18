# jcg03
Task Dask

# Task Desk — Python GUI project

A desktop task manager built with Tkinter and SQLite. No pip packages or
internet connection are needed to use it.

## Run in VSCodium or VS Code

1. Install Python 3.10 or newer. On Windows, enable **Add Python to PATH**.
2. Extract this ZIP and open the `task_manager` folder in your editor.
3. Open the editor's terminal and run:

   ```sh
   python task_manager.py
   ```

   On Windows, `py task_manager.py` also works. On macOS or Linux,
   you may need `python3 task_manager.py`.

If Python reports that Tkinter is missing, install Python with Tcl/Tk support.
On Ubuntu/Debian, use `sudo apt install python3-tk`.
This is a desktop application and needs a graphical desktop session.

## Features

- Add, edit, delete, complete, and reopen tasks.
- High, Medium, and Low priorities; active high-priority tasks appear first.
- Search task titles and filter by completion status.
- Automatic local saving through SQLite, even after closing the app.
- Toggle **Dark mode** at the top right. The entire main window updates
  immediately and your choice is remembered next time you open Task Desk.
  Native operating-system message boxes may follow your system appearance.
- Resize the window and scroll long task lists.
- Ctrl+N clears the editor; Ctrl+F focuses search; Enter saves a task.
- Double-click a task to edit it. Click Clear to cancel editing.

Task names are limited to 160 characters. Delete asks for confirmation.
Tasks are stored in `%LOCALAPPDATA%/TaskDesk/tasks.sqlite3` on Windows,
or `$XDG_DATA_HOME/TaskDesk/tasks.sqlite3` on other systems, falling back
to `~/.local/share/TaskDesk/tasks.sqlite3`.

## How the project works

`TaskStore` manages the database, validation, and saved changes.
`TaskDesk` creates the window and connects buttons to Python methods.
`refresh()` rebuilds the visible task list from saved data and the filters.
The `main()` function starts the application.

To customize the interface, change the colors in `setup_style()` and the
window size in `TaskDesk.__init__()`.
