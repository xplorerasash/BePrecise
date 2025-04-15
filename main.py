import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import json
import os
from math import ceil

# File paths
TASK_FILE = "data.json"
PLANNER_FILE = "planner_data.json"

# Ensure JSON files exist and migrate old data if needed
def migrate_task_data(task_data):
    """Convert old task format to new format"""
    migrated = {}
    for title, task in task_data.items():
        # Handle old format where 'minutes' was used instead of 'total_minutes'
        if 'minutes' in task and 'total_minutes' not in task:
            task['total_minutes'] = task.pop('minutes')
        
        # Set default values for missing keys
        defaults = {
            'total_minutes': 0,
            'daily_minutes': 0,
            'completed_minutes': 0,
            'completed': False,
            'type': 'Daily',
            'created': datetime.now().strftime("%Y-%m-%d")
        }
        
        # Create new task with defaults where needed
        new_task = {**defaults, **task}
        
        # Calculate daily minutes if not set
        if new_task['daily_minutes'] == 0:
            new_task['daily_minutes'] = distribute_time(
                new_task['type'],
                new_task['total_minutes'],
                new_task.get('deadline', datetime.now().strftime("%Y-%m-%d"))
            )
        
        migrated[title] = new_task
    return migrated
# Load and save functions
def load_tasks():
    try:
        with open(TASK_FILE, "r") as f:
            data = json.load(f)
            # Migrate old data to new format
            return migrate_task_data(data) if isinstance(data, dict) else {}
    except:
        return {}
    

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def load_schedule():
    try:
        with open(PLANNER_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def save_schedule(schedule):
    with open(PLANNER_FILE, "w") as f:
        json.dump(schedule, f, indent=4)

# Main application
app = tk.Tk()
app.title("BePrecise")
app.geometry("1000x750")

notebook = ttk.Notebook(app)
notebook.pack(fill="both", expand=True)

# ---------------------- Task Manager Tab ----------------------
main_tab = ttk.Frame(notebook)
notebook.add(main_tab, text="📋 Task Manager")

tasks = load_tasks()  

# Task Entry Section
entry_frame = ttk.LabelFrame(main_tab, text="Add New Task")
entry_frame.pack(pady=10, padx=10, fill="x")

# Task Title
ttk.Label(entry_frame, text="Task Title:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry = ttk.Entry(entry_frame, width=40)
entry.grid(row=0, column=1, padx=5, pady=5)  


# Time Required
ttk.Label(entry_frame, text="Minutes Required:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
hour_entry = ttk.Entry(entry_frame, width=15)
hour_entry.grid(row=0, column=3, padx=5, pady=5)
hour_entry.insert(0, "0")

# Deadline
ttk.Label(entry_frame, text="Deadline:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
date_picker = DateEntry(entry_frame, width=12, date_pattern="yyyy-mm-dd")
date_picker.grid(row=0, column=5, padx=5, pady=5)

# Task Type
ttk.Label(entry_frame, text="Task Type:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
type_box = ttk.Combobox(entry_frame, values=["Daily", "Weekly", "Monthly"], state="readonly", width=10)
type_box.grid(row=0, column=7, padx=5, pady=5)
type_box.set("Daily")

# Add Task Button
add_btn = ttk.Button(entry_frame, text="Add Task", command=lambda: add_task())
add_btn.grid(row=0, column=8, padx=5, pady=5)

# Search Section
search_frame = ttk.LabelFrame(main_tab, text="Search Tasks")
search_frame.pack(pady=5, padx=10, fill="x")

ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
search_entry = ttk.Entry(search_frame, width=30)
search_entry.pack(side="left", padx=5)

# Task List Section
list_frame = ttk.LabelFrame(main_tab, text="Task List")
list_frame.pack(pady=10, padx=10, fill="both", expand=True)

result_frame = ttk.Frame(list_frame)
result_frame.pack(fill="both", expand=True)

def distribute_time(task_type, total_minutes, deadline):
    """Distribute time based on task type"""
    deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    today = datetime.now().date()
    
    if task_type == "Daily":
        return total_minutes
    elif task_type == "Weekly":
        days_left = (deadline_date - today).days + 1
        weeks_left = ceil(days_left / 7)
        return ceil(total_minutes / weeks_left)
    elif task_type == "Monthly":
        months_left = (deadline_date.year - today.year) * 12 + (deadline_date.month - today.month)
        if deadline_date.day > today.day:
            months_left += 1
        months_left = max(months_left, 1)
        return ceil(total_minutes / months_left)
    return total_minutes

def add_task():
    title = entry.get().strip()
    try:
        minutes = int(hour_entry.get().strip())
        if minutes <= 0:
            raise ValueError
    except:
        messagebox.showerror("Error", "Enter a valid positive number for minutes")
        return

    deadline = date_picker.get_date().strftime("%Y-%m-%d")
    task_type = type_box.get()

    if title:
        daily_minutes = distribute_time(task_type, minutes, deadline)
        
        tasks[title] = {
            "total_minutes": minutes,
            "daily_minutes": daily_minutes,
            "deadline": deadline,
            "completed_minutes": 0,
            "type": task_type,
            "completed": False,
            "created": datetime.now().strftime("%Y-%m-%d")
        }
        save_tasks(tasks)
        refresh_tasks()
        entry.delete(0, tk.END)
        hour_entry.delete(0, tk.END)
        hour_entry.insert(0, "0")

def refresh_tasks():
    for widget in result_frame.winfo_children():
        widget.destroy()

    keyword = search_entry.get().lower()

    if not tasks:
        ttk.Label(result_frame, text="No tasks found").pack(pady=20)
        return

    for idx, (title, task) in enumerate(tasks.items()):
        if keyword and keyword not in title.lower():
            continue

        frame = ttk.Frame(result_frame)
        frame.pack(fill="x", pady=2, padx=5)

        # Safely get values with defaults
        total_mins = task.get('total_minutes', 0)
        completed_mins = task.get('completed_minutes', 0)
        rem_total = max(total_mins - completed_mins, 0)
        
        deadline = task.get('deadline', datetime.now().strftime("%Y-%m-%d"))
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
        remaining_days = max((deadline_date - datetime.now()).days + 1, 1)
        
        daily_target = task.get('daily_minutes', total_mins)
        status = (f"Total: {total_mins} min | Daily Target: {daily_target} min | "
                 f"Completed: {completed_mins} min | Days Left: {remaining_days}")
        
        label = ttk.Label(frame, text=f"{title} ({task.get('type', 'Daily')}) - {status}", width=100)
        label.pack(side="left")

        def update_done(t=title):
            try:
                done = int(simpledialog.askstring("Update", f"How many minutes did you complete for '{t}'?") or "0")
            except:
                return
            tasks[t]['completed_minutes'] = tasks[t].get('completed_minutes', 0) + done
            save_tasks(tasks)
            refresh_tasks()

        def toggle_complete(t=title):
            tasks[t]['completed'] = not tasks[t].get('completed', False)
            save_tasks(tasks)
            refresh_tasks()

        def edit_task(t=title):
            new_title = simpledialog.askstring("Edit", "New title:", initialvalue=t)
            if new_title and new_title != t:
                tasks[new_title] = tasks.pop(t)
                save_tasks(tasks)
                refresh_tasks()

        def delete_task(t=title):
            if messagebox.askyesno("Delete", f"Delete task '{t}'?"):
                tasks.pop(t)
                save_tasks(tasks)
                refresh_tasks()

        ttk.Button(frame, text="Update", command=update_done).pack(side="left", padx=2)
        ttk.Button(frame, text="Edit", command=edit_task).pack(side="left", padx=2)
        ttk.Button(frame, text="Delete", command=delete_task).pack(side="left", padx=2)
        ttk.Button(frame, 
                  text="Mark Complete" if not task.get('completed') else "Mark Incomplete", 
                  command=toggle_complete).pack(side="left", padx=2)

search_entry.bind("<KeyRelease>", lambda e: refresh_tasks())
refresh_tasks()

# ---------------------- Daily Planner Tab ----------------------
planner_tab = ttk.Frame(notebook)
notebook.add(planner_tab, text="🗓️ Daily Planner")

planner_top = ttk.Frame(planner_tab)
planner_top.pack(pady=10, padx=10, fill="x")

# Date Selection
ttk.Label(planner_top, text="Select Date:").pack(side="left")
planner_date = DateEntry(planner_top, width=12, date_pattern="yyyy-mm-dd")
planner_date.pack(side="left", padx=5)

# Time Allocation Info
time_info_frame = ttk.LabelFrame(planner_tab, text="Time Allocation")
time_info_frame.pack(pady=5, padx=10, fill="x")

ttk.Label(time_info_frame, text="Total Available Time: 24 hours (1440 minutes)").pack(side="left", padx=5)
allocated_label = ttk.Label(time_info_frame, text="Allocated Time: 0 minutes")
allocated_label.pack(side="left", padx=20)
remaining_label = ttk.Label(time_info_frame, text="Remaining Time: 1440 minutes")
remaining_label.pack(side="left", padx=20)

# Planner Grid
planner_frame = ttk.LabelFrame(planner_tab, text="Daily Schedule")
planner_frame.pack(pady=10, padx=10, fill="both", expand=True)

def calculate_time_usage(schedule):
    total = 0
    for slot in schedule.values():
        if slot.get("task") and slot.get("duration"):
            try:
                total += int(slot["duration"])
            except:
                pass
    return total

def refresh_day_plan():
    for widget in planner_frame.winfo_children():
        widget.destroy()

    selected_date = planner_date.get_date().strftime("%Y-%m-%d")
    schedule = load_schedule().get(selected_date, {})
    
    total_allocated = calculate_time_usage(schedule)
    allocated_label.config(text=f"Allocated Time: {total_allocated} minutes")
    remaining_label.config(text=f"Remaining Time: {1440 - total_allocated} minutes")

    for hour in range(24):
        time_slot = f"{hour:02d}:00"
        slot_data = schedule.get(time_slot, {})
        
        frame = ttk.Frame(planner_frame)
        frame.pack(fill="x", pady=2, padx=5)

        ttk.Label(frame, text=time_slot, width=8).pack(side="left")

        # Task Entry
        task_var = tk.StringVar(value=slot_data.get("task", ""))
        entry = ttk.Entry(frame, textvariable=task_var, width=40)
        entry.pack(side="left", padx=5)

        # Duration Entry
        duration_var = tk.StringVar(value=slot_data.get("duration", "0"))
        duration = ttk.Spinbox(frame, from_=0, to=1440, textvariable=duration_var, width=5)
        duration.pack(side="left", padx=5)
        ttk.Label(frame, text="minutes").pack(side="left")

        def save_slot(h=hour, t=task_var, d=duration_var):
            selected_date = planner_date.get_date().strftime("%Y-%m-%d")
            full_schedule = load_schedule()
            if selected_date not in full_schedule:
                full_schedule[selected_date] = {}

            task_text = t.get().strip()
            duration_text = d.get().strip()
            
            if task_text and duration_text:
                try:
                    duration_min = int(duration_text)
                    if duration_min <= 0:
                        full_schedule[selected_date].pop(f"{h:02d}:00", None)
                    else:
                        full_schedule[selected_date][f"{h:02d}:00"] = {
                            "task": task_text,
                            "duration": duration_text
                        }
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid number for duration")
                    return
            else:
                full_schedule[selected_date].pop(f"{h:02d}:00", None)

            save_schedule(full_schedule)
            refresh_day_plan()

        ttk.Button(frame, text="Save", command=save_slot).pack(side="left", padx=5)

planner_date.bind("<<DateEntrySelected>>", lambda e: refresh_day_plan())
refresh_day_plan()

# ---------------------- Summary Tab ----------------------
dashboard_tab = ttk.Frame(notebook)
notebook.add(dashboard_tab, text="📊 Summary View")

summary_frame = ttk.Frame(dashboard_tab)
summary_frame.pack(fill="both", expand=True, padx=10, pady=10)

def render_summary():
    for widget in summary_frame.winfo_children():
        widget.destroy()

    if not tasks:
        ttk.Label(summary_frame, text="No tasks to display").pack(pady=20)
        return

    # Categorize tasks
    categories = {"Daily": [], "Weekly": [], "Monthly": []}
    for title, task in tasks.items():
        categories[task['type']].append((title, task))

    # Display each category
    for category, items in categories.items():
        if not items:
            continue

        frame = ttk.LabelFrame(summary_frame, text=f"{category} Tasks")
        frame.pack(fill="x", padx=5, pady=5)

        for title, task in items:
            completed = task.get('completed_minutes', 0)
            total = task['total_minutes']
            progress = min(completed / total * 100, 100) if total > 0 else 0
            
            # Task info
            task_frame = ttk.Frame(frame)
            task_frame.pack(fill="x", pady=2)
            
            ttk.Label(task_frame, text=title, width=30).pack(side="left")
            
            # Progress bar
            pb = ttk.Progressbar(task_frame, orient="horizontal", length=200, mode="determinate")
            pb['value'] = progress
            pb.pack(side="left", padx=5)
            
            # Progress text
            ttk.Label(task_frame, text=f"{completed}/{total} min ({progress:.1f}%)").pack(side="left")

notebook.bind("<<NotebookTabChanged>>", lambda e: render_summary())

app.mainloop()