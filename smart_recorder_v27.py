import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import pyautogui
from pynput import mouse, keyboard
import time
import threading
import json
import os
import ctypes
import shutil
import pyperclip 
import math
from PIL import Image, ImageTk

# --- DPI FIX ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

# --- SETTINGS ---
pyautogui.FAILSAFE = False 
MACRO_ROOT = "saved_macros_local"

if not os.path.exists(MACRO_ROOT):
    os.makedirs(MACRO_ROOT)

# --- THEME ---
BG_COLOR = "#ffffff"       
FG_COLOR = "#333333"       
HEADER_BG = "#f1f2f6"      
BTN_REC = "#ff4757"
BTN_STOP = "#2f3542"
BTN_PLAY = "#2ed573"
BTN_SEG = "#f39c12"
BTN_DEL = "#a4b0be"

class BlinkingIndicator:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.win.geometry(f"20x20+{screen_width - 40}+{screen_height - 60}")
        self.win.config(bg="white")
        try:
            self.win.attributes("-transparentcolor", "white")
        except: pass
        self.canvas = tk.Canvas(self.win, width=20, height=20, bg="white", highlightthickness=0)
        self.canvas.pack()
        self.dot = self.canvas.create_oval(2, 2, 18, 18, fill="red", outline="red")
        self.win.withdraw()
        self.is_blinking = False
        self.current_color = "red"

    def toggle_blink(self):
        if self.is_blinking:
            current_c = self.canvas.itemcget(self.dot, "fill")
            next_color = "white" if current_c == self.current_color else self.current_color
            self.canvas.itemconfig(self.dot, fill=next_color, outline=next_color)
            self.root.after(600, self.toggle_blink)

    def start(self, color="red"):
        self.current_color = color
        self.canvas.itemconfig(self.dot, fill=color, outline=color)
        self.is_blinking = True
        self.win.deiconify()
        self.toggle_blink()

    def stop(self):
        self.is_blinking = False
        self.win.withdraw()

class MacroRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Bot v27 (Play/Pause Edition)")
        self.root.geometry("400x650") 
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        self.is_recording = False
        self.is_paused = False 
        self.stop_playback_flag = False
        self.pause_playback_flag = False # අලුත් Pause Playback Flag එක
        self.events = []
        self.start_time = 0
        self.mouse_listener = None
        self.keyboard_listener = None
        self.current_task_folder = ""
        self.img_counter = 0
        
        self.indicator = BlinkingIndicator(self.root)
        
        # --- UI SETUP ---
        header = tk.Frame(root, bg=HEADER_BG, pady=15, padx=15)
        header.pack(fill="x")
        
        title_frame = tk.Frame(header, bg=HEADER_BG)
        title_frame.pack(side="left")
        tk.Label(title_frame, text="Smart Bot v27", font=("Segoe UI", 14, "bold"), bg=HEADER_BG, fg="#2c3e50").pack(anchor="w")
        tk.Label(title_frame, text="Playback Pause Supported", font=("Arial", 9), bg=HEADER_BG, fg="purple").pack(anchor="w")

        self.btn_menu = tk.Button(header, text="☰", font=("Arial", 16, "bold"), bg=HEADER_BG, fg="#333", bd=0, cursor="hand2", command=self.show_shortcuts)
        self.btn_menu.pack(side="right")

        main_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Select Task:", font=("Arial", 9, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w")
        sel_frame = tk.Frame(main_frame, bg=BG_COLOR)
        sel_frame.pack(fill="x", pady=5)
        self.combo_workflows = ttk.Combobox(sel_frame, state="readonly", font=("Arial", 10))
        self.combo_workflows.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_delete = tk.Button(sel_frame, text="🗑️", bg=BTN_DEL, fg="white", font=("Arial", 9), bd=0, width=4, command=self.delete_workflow)
        self.btn_delete.pack(side="right")
        self.refresh_workflows()

        tk.Label(main_frame, text="Create New Task:", font=("Arial", 9, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w", pady=(15, 0))
        self.entry_name = tk.Entry(main_frame, font=("Arial", 11), bg="#f1f2f6", fg="black", relief="flat")
        self.entry_name.pack(fill="x", pady=5, ipady=5)

        self.btn_record = tk.Button(main_frame, text="🔴  RECORD NEW TASK", bg=BTN_REC, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", command=self.start_recording)
        self.btn_record.pack(fill="x", pady=(15, 5), ipady=5)

        self.btn_stop = tk.Button(main_frame, text="⬛  STOP (Esc)", bg=BTN_STOP, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", command=self.request_stop)
        self.btn_stop.pack(fill="x", pady=5, ipady=5)

        # Loop Count UI
        loop_frame = tk.Frame(main_frame, bg=BG_COLOR)
        loop_frame.pack(fill="x", pady=(5, 5))
        tk.Label(loop_frame, text="Repeat Count (Loop):", font=("Arial", 9, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(side="left")
        self.loop_var = tk.IntVar(value=1)
        self.spin_loop = ttk.Spinbox(loop_frame, from_=1, to=9999, textvariable=self.loop_var, width=8, font=("Arial", 10))
        self.spin_loop.pack(side="right")

        self.btn_play = tk.Button(main_frame, text="▶  PLAY FULL TASK", bg=BTN_PLAY, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", command=lambda: self.start_playback_thread())
        self.btn_play.pack(fill="x", pady=5, ipady=5)

        # --- TIMELINE BUTTON ---
        self.btn_timeline = tk.Button(main_frame, text="✂️  TIMELINE & EDIT ACTIONS", bg=BTN_SEG, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", command=self.open_timeline)
        self.btn_timeline.pack(fill="x", pady=5, ipady=5)

        self.status_label = tk.Label(root, text="Ready", bg="#f1f2f6", fg="#333", font=("Arial", 9), pady=8)
        self.status_label.pack(fill="x", side="bottom")

    # --- TIMELINE UI & LOGIC (Unchanged from previous) ---
    def open_timeline(self):
        folder = self.combo_workflows.get()
        if not folder: 
            messagebox.showwarning("Warning", "Please select a task first!")
            return
        
        self.current_edit_folder = folder
        self.current_edit_json = os.path.join(MACRO_ROOT, folder, "data.json")
        if not os.path.exists(self.current_edit_json): return
        
        with open(self.current_edit_json, 'r') as f:
            self.timeline_events = json.load(f)

        if not self.timeline_events:
            messagebox.showinfo("Empty", "This task has no recorded actions.")
            return

        self.tl_win = tk.Toplevel(self.root)
        self.tl_win.title(f"Timeline Editor - {folder}")
        self.tl_win.geometry("850x600")
        self.tl_win.configure(bg=HEADER_BG)
        self.tl_win.transient(self.root)

        left_frame = tk.Frame(self.tl_win, bg=HEADER_BG)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        cols = ("ID", "Action Type", "Detail", "Delay(s)")
        self.tree = ttk.Treeview(left_frame, columns=cols, show="headings", selectmode="browse")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Action Type", width=100)
        self.tree.column("Detail", width=150)
        self.tree.column("Delay(s)", width=60, anchor="center")
        
        vsb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tl_refresh_tree()

        right_frame = tk.Frame(self.tl_win, bg=HEADER_BG, width=320)
        right_frame.pack(side="right", fill="y", padx=10, pady=10)

        tk.Label(right_frame, text="Screenshot Preview", bg=HEADER_BG, font=("Arial", 10, "bold")).pack()
        self.img_label = tk.Label(right_frame, bg="#dfe6e9", width=40, height=14, text="No Image available\nfor this action", fg="#636e72")
        self.img_label.pack(pady=5)

        self.seg_start = 0
        self.seg_end = len(self.timeline_events) - 1

        info_frame = tk.Frame(right_frame, bg="white", bd=1, relief="solid")
        info_frame.pack(fill="x", pady=5)
        self.lbl_start = tk.Label(info_frame, text=f"Start Action: {self.seg_start}", bg="white", font=("Arial", 9))
        self.lbl_start.pack(anchor="w", padx=5, pady=2)
        self.lbl_end = tk.Label(info_frame, text=f"End Action: {self.seg_end}", bg="white", font=("Arial", 9))
        self.lbl_end.pack(anchor="w", padx=5, pady=2)

        def on_select(event):
            sel = self.tree.selection()
            if not sel: return
            idx = int(sel[0])
            ev = self.timeline_events[idx]
            
            if ev.get('image'):
                img_path = os.path.join(MACRO_ROOT, self.current_edit_folder, ev['image'])
                if os.path.exists(img_path):
                    try:
                        img = Image.open(img_path)
                        img.thumbnail((250, 250), Image.Resampling.LANCZOS) 
                        photo = ImageTk.PhotoImage(img)
                        self.img_label.config(image=photo, text="", width=250, height=250)
                        self.img_label.image = photo 
                    except Exception:
                        self.img_label.config(image='', text="Error loading image", width=40, height=14)
            else:
                self.img_label.config(image='', text="No Image available", width=40, height=14)

        self.tree.bind('<<TreeviewSelect>>', on_select)

        seg_frame = tk.Frame(right_frame, bg=HEADER_BG)
        seg_frame.pack(fill="x", pady=5)
        tk.Button(seg_frame, text="📍 START Point", bg="#3498db", fg="white", font=("Arial", 8, "bold"), relief="flat", command=self.set_start).pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(seg_frame, text="📍 END Point", bg="#e74c3c", fg="white", font=("Arial", 8, "bold"), relief="flat", command=self.set_end).pack(side="right", fill="x", expand=True, padx=2)
        
        edit_frame = tk.LabelFrame(right_frame, text="✏️ Edit Tools", bg="white", font=("Arial", 9, "bold"))
        edit_frame.pack(fill="x", pady=10)
        
        tk.Button(edit_frame, text="🗑️ Delete Selected Action", bg=BTN_DEL, fg="white", font=("Arial", 9), relief="flat", command=self.tl_delete_action).pack(fill="x", pady=3, padx=5)
        tk.Button(edit_frame, text="⏱️ Edit Wait Time (Delay)", bg="#f39c12", fg="white", font=("Arial", 9), relief="flat", command=self.tl_edit_delay).pack(fill="x", pady=3, padx=5)
        tk.Button(edit_frame, text="➕ Record 1 Action & Insert", bg="#9b59b6", fg="white", font=("Arial", 9), relief="flat", command=self.tl_insert_action).pack(fill="x", pady=3, padx=5)

        def play_segment():
            self.tl_win.destroy()
            self.start_playback_thread(start_idx=self.seg_start, end_idx=self.seg_end)

        tk.Button(right_frame, text="▶ PLAY SEGMENT", bg=BTN_PLAY, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", command=play_segment).pack(fill="x", side="bottom", pady=5, ipady=8)

    def tl_refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, ev in enumerate(self.timeline_events):
            detail = ev.get('key') or ev.get('button') or ev.get('text') or ""
            if ev['type'] == 'scroll': detail = f"dy: {ev.get('dy', 0)}"
            self.tree.insert("", "end", iid=str(i), values=(i, ev['type'].upper(), detail, round(ev['delay'], 2)))

    def tl_save(self):
        with open(self.current_edit_json, 'w') as f:
            json.dump(self.timeline_events, f)

    def set_start(self):
        sel = self.tree.selection()
        if sel: 
            idx = int(sel[0])
            if idx > self.seg_end: return messagebox.showwarning("Warning", "Start point cannot be after End point!")
            self.seg_start = idx
            self.lbl_start.config(text=f"Start Action: {self.seg_start}")
            
    def set_end(self):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            if idx < self.seg_start: return messagebox.showwarning("Warning", "End point cannot be before Start point!")
            self.seg_end = idx
            self.lbl_end.config(text=f"End Action: {self.seg_end}")

    def tl_delete_action(self):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        del self.timeline_events[idx]
        if self.seg_end >= len(self.timeline_events):
            self.seg_end = max(0, len(self.timeline_events) - 1)
        self.lbl_end.config(text=f"End Action: {self.seg_end}")
        self.tl_save()
        self.tl_refresh_tree()
        self.img_label.config(image='', text="Action Deleted")

    def tl_edit_delay(self):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        curr_delay = self.timeline_events[idx]['delay']
        new_delay = simpledialog.askfloat("Edit Delay", f"Action #{idx}\nCurrent Delay: {round(curr_delay,2)}s\nEnter new delay (seconds):", initialvalue=round(curr_delay, 2))
        if new_delay is not None and new_delay >= 0:
            self.timeline_events[idx]['delay'] = new_delay
            self.tl_save()
            self.tl_refresh_tree()

    def tl_insert_action(self):
        sel = self.tree.selection()
        if not sel: 
            return messagebox.showinfo("Select", "Please select an action from the list first.\nThe new action will be inserted above it.")
        idx = int(sel[0])

        messagebox.showinfo("Insert Action", "The bot will minimize.\n\nMake exactly ONE mouse click OR press ONE keyboard key.\nIt will be automatically recorded and inserted at position #" + str(idx) + ".")
        
        self.tl_win.withdraw()
        self.root.iconify()
        
        self.temp_action = {}
        self.temp_ml = None
        self.temp_kl = None
        
        def on_click(x, y, button, pressed):
            if pressed:
                self.temp_action['type'] = 'click'
                self.temp_action['x'] = x
                self.temp_action['y'] = y
                self.temp_action['button'] = str(button).replace("Button.", "")
                self.temp_action['delay'] = 1.0 
                if self.temp_kl: self.temp_kl.stop()
                return False

        def on_press(key):
            self.temp_action['type'] = 'key_down'
            self.temp_action['key'] = self.resolve_key(key)
            self.temp_action['delay'] = 1.0
            if self.temp_ml: self.temp_ml.stop()
            return False
            
        self.temp_ml = mouse.Listener(on_click=on_click)
        self.temp_kl = keyboard.Listener(on_press=on_press)
        self.temp_ml.start()
        self.temp_kl.start()
        
        def wait_for_capture():
            if not self.temp_action:
                self.root.after(100, wait_for_capture)
            else:
                self.timeline_events.insert(idx, self.temp_action)
                if self.temp_action['type'] == 'key_down':
                    up_action = self.temp_action.copy()
                    up_action['type'] = 'key_up'
                    up_action['delay'] = 0.1
                    self.timeline_events.insert(idx+1, up_action)
                self.tl_save()
                self.root.deiconify()
                self.tl_win.deiconify()
                self.tl_refresh_tree()

        self.root.after(100, wait_for_capture)

    # --- OTHER METHODS ---
    def show_shortcuts(self):
        msg = """
📢 CONTROLS:
• Esc : Stop Recording OR Stop Playback
• F8  : Auto Paste Text (Sinhala/English)
• F9  : Pause / Resume (Works for both Record & Play)

⌨️ SUPPORTED SHORTCUTS:
• Ctrl + A : Select All
• Ctrl + C : Copy
• Ctrl + V : Paste
• Ctrl + Z : Undo
• Ctrl + S : Save
        """
        messagebox.showinfo("Smart Bot Shortcuts", msg)

    def refresh_workflows(self):
        if not os.path.exists(MACRO_ROOT): return
        folders = [d for d in os.listdir(MACRO_ROOT) if os.path.isdir(os.path.join(MACRO_ROOT, d))]
        self.combo_workflows['values'] = folders
        if folders: self.combo_workflows.current(0)
        else: self.combo_workflows.set('')

    def delete_workflow(self):
        name = self.combo_workflows.get()
        if not name: return
        if messagebox.askyesno("Confirm", f"Delete '{name}'?"):
            try:
                shutil.rmtree(os.path.join(MACRO_ROOT, name))
                self.refresh_workflows()
            except: pass

    # --- RECORDING LOGIC ---
    def start_recording(self):
        name = self.entry_name.get().strip()
        if not name: return
        self.current_task_folder = os.path.join(MACRO_ROOT, name)
        if os.path.exists(self.current_task_folder): shutil.rmtree(self.current_task_folder)
        os.makedirs(self.current_task_folder)

        self.events = []
        self.img_counter = 0
        self.is_recording = True
        self.is_paused = False
        self.start_time = time.time()
        
        self.status_label.config(text="Recording... (Esc: Stop | F9: Pause)", fg="red")
        self.toggle_buttons(True)
        self.root.iconify()
        self.indicator.start("red") 
        self.start_listeners()

    def request_stop(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.stop_playback_flag = True 
            self.status_label.config(text="Stopping...", fg="orange")

    def stop_recording(self):
        if not self.is_recording: return
        self.is_recording = False
        self.is_paused = False
        self.indicator.stop()
        
        if self.mouse_listener: self.mouse_listener.stop()
        if self.keyboard_listener: self.keyboard_listener.stop()

        with open(os.path.join(self.current_task_folder, "data.json"), 'w') as f:
            json.dump(self.events, f)

        self.root.deiconify()
        self.refresh_workflows()
        self.combo_workflows.set(os.path.basename(self.current_task_folder))
        self.status_label.config(text="Recording Saved!", fg="green")
        self.toggle_buttons(False)

    def toggle_buttons(self, recording):
        state = "disabled" if recording else "normal"
        self.btn_record.config(state=state)
        self.btn_play.config(state=state)
        self.btn_timeline.config(state=state)
        self.spin_loop.config(state=state)

    def start_listeners(self):
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def on_click(self, x, y, button, pressed):
        if not self.is_recording or self.is_paused: return
        if pressed:
            elapsed = time.time() - self.start_time
            self.start_time = time.time()
            btn_str = str(button).replace("Button.", "")
            
            img_filename = f"click_{self.img_counter}.png"
            try:
                region_size = 200 
                screen_w, screen_h = pyautogui.size()
                region_left = max(0, min(int(x - region_size/2), screen_w - region_size))
                region_top = max(0, min(int(y - region_size/2), screen_h - region_size))
                
                pyautogui.screenshot(os.path.join(self.current_task_folder, img_filename), 
                                   region=(region_left, region_top, region_size, region_size))
            except: img_filename = None

            self.events.append({
                "type": "click", "x": x, "y": y, "button": btn_str, 
                "image": img_filename, "delay": elapsed
            })
            self.img_counter += 1

    def on_scroll(self, x, y, dx, dy):
        if not self.is_recording or self.is_paused: return
        elapsed = time.time() - self.start_time
        self.start_time = time.time()
        self.events.append({"type": "scroll", "x": x, "y": y, "dx": dx, "dy": dy, "delay": elapsed})

    def on_press(self, key):
        if not self.is_recording: return
        if key == keyboard.Key.f9:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.indicator.stop()
                self.status_label.config(text="Recording PAUSED... Press F9 to Resume", fg="orange")
            else:
                self.start_time = time.time() 
                self.indicator.start("red")
                self.status_label.config(text="Recording... (Esc: Stop | F9: Pause)", fg="red")
            return
        if self.is_paused: return
        if key == keyboard.Key.f8:
            self.root.after(0, self._show_dialog)
            return
            
        elapsed = time.time() - self.start_time
        self.start_time = time.time()
        key_char = self.resolve_key(key)
        self.events.append({"type": "key_down", "key": key_char, "delay": elapsed})

    def on_release(self, key):
        if not self.is_recording: return
        if key == keyboard.Key.esc:
            self.stop_recording()
            return False
            
        if key == keyboard.Key.f9: return 
        if self.is_paused: return
        if key == keyboard.Key.f8: return
        
        elapsed = time.time() - self.start_time
        self.start_time = time.time()
        key_char = self.resolve_key(key)
        self.events.append({"type": "key_up", "key": key_char, "delay": elapsed})

    def resolve_key(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                code = ord(key.char)
                if code == 1: return 'a'  
                if code == 3: return 'c'  
                if code == 19: return 's' 
                if code == 22: return 'v' 
                if code == 24: return 'x' 
                if code == 26: return 'z' 
                return key.char
        except: pass
        k = str(key).replace("'", "")
        if "Key." in k: return k.replace("Key.", "")
        return k

    def _show_dialog(self):
        was_paused = self.is_paused
        self.is_paused = True 
        text = simpledialog.askstring("Auto Type", "Enter Text:")
        if text:
            elapsed = time.time() - self.start_time
            self.start_time = time.time()
            self.events.append({"type": "smart_paste", "text": text, "delay": elapsed})
        self.is_paused = was_paused
        self.start_time = time.time() 


    # --- PLAYBACK LOGIC ---
    def start_playback_thread(self, start_idx=0, end_idx=None):
        self.stop_playback_flag = False
        self.pause_playback_flag = False
        threading.Thread(target=self.play_macro, args=(start_idx, end_idx), daemon=True).start()

    # මේක අලුතින් හදපු custom delay function එක (Pause/Resume support කරනවා)
    def wait_with_pause(self, delay, status_text):
        target_time = time.time() + delay
        while time.time() < target_time:
            if self.stop_playback_flag:
                break
            
            if self.pause_playback_flag:
                # Pause කරාම ඉතුරු වෙලා තියෙන වෙලාව ගණන් හදාගන්නවා
                remaining = target_time - time.time()
                
                self.root.after(0, lambda: self.indicator.start("orange"))
                self.root.after(0, lambda: self.status_label.config(text="Playback PAUSED... (F9: Resume | Esc: Stop)", fg="orange"))
                
                # F9 ආයෙත් ඔබනකම් මේක ඇතුලෙම හිරවෙලා ඉන්නවා (Pause state)
                while self.pause_playback_flag and not self.stop_playback_flag:
                    time.sleep(0.1)
                
                # Resume කරාට පස්සේ...
                self.root.after(0, lambda: self.indicator.start("green"))
                self.root.after(0, lambda: self.status_label.config(text=status_text, fg=BTN_PLAY))
                
                # අර කලින් ඉතුරු වුණු වෙලාව ආයේ target එකට දානවා
                target_time = time.time() + remaining
                
            time.sleep(0.01)


    def play_macro(self, start_idx=0, end_idx=None):
        folder = self.combo_workflows.get()
        if not folder: return
        json_path = os.path.join(MACRO_ROOT, folder, "data.json")
        if not os.path.exists(json_path): return

        try:
            loop_count = self.loop_var.get()
            if loop_count < 1: loop_count = 1
        except:
            loop_count = 1

        self.root.after(0, lambda: self.toggle_buttons(True))
        self.root.after(0, self.root.iconify)
        self.root.after(0, lambda: self.indicator.start("green")) 

        def on_pb_release(key):
            if key == keyboard.Key.esc:
                self.stop_playback_flag = True
                return False 
            elif key == keyboard.Key.f9:
                self.pause_playback_flag = not self.pause_playback_flag # Toggle Pause/Resume

        pb_listener = keyboard.Listener(on_release=on_pb_release)
        pb_listener.start()

        try:
            with open(json_path, 'r') as f:
                all_events = json.load(f)

            if end_idx is None or end_idx >= len(all_events):
                end_idx = len(all_events) - 1

            events_to_play = all_events[start_idx : end_idx + 1]

            if events_to_play and events_to_play[0]['delay'] > 1.0:
                events_to_play[0]['delay'] = 0.5

            for current_loop in range(loop_count):
                if self.stop_playback_flag: break
                
                segment_info = f" (Segment {start_idx}-{end_idx})" if (start_idx > 0 or end_idx < len(all_events)-1) else ""
                current_status_text = f"Playing '{folder}'{segment_info}... Loop {current_loop+1}/{loop_count} (Esc: Stop | F9: Pause)"
                
                self.root.after(0, lambda msg=current_status_text: self.status_label.config(text=msg, fg=BTN_PLAY))

                for action in events_to_play:
                    if self.stop_playback_flag: break

                    # පරණ time.sleep වෙනුවට අලුත් pause support කරන wait function එක දානවා
                    self.wait_with_pause(action['delay'], current_status_text)
                    
                    if self.stop_playback_flag: break

                    if action['type'] == 'click':
                        tx, ty = action['x'], action['y']
                        if action.get('image'):
                            img_path = os.path.join(MACRO_ROOT, folder, action['image'])
                            if os.path.exists(img_path):
                                try:
                                    loc = pyautogui.locateCenterOnScreen(img_path, confidence=0.9, grayscale=True)
                                    if loc:
                                        dist = math.hypot(loc.x - tx, loc.y - ty)
                                        if dist < 50: tx, ty = loc
                                except: pass
                        
                        btn = action['button']
                        if btn not in ['left', 'middle', 'right']: btn = 'left'
                        
                        pyautogui.moveTo(tx, ty, duration=0.1)
                        pyautogui.mouseDown(button=btn)
                        time.sleep(0.08) 
                        pyautogui.mouseUp(button=btn)

                    elif action['type'] == 'smart_paste':
                        pyperclip.copy(action['text'])
                        time.sleep(0.1)
                        pyautogui.hotkey('ctrl', 'v')

                    elif action['type'] == 'scroll':
                        if 'x' in action:
                            pyautogui.moveTo(action['x'], action['y'], duration=0.1)
                        pyautogui.scroll(int(action['dy'] * 120))

                    elif action['type'] == 'key_down':
                        k = self.clean_key(action['key'])
                        pyautogui.keyDown(k)
                        if k in ['ctrl', 'alt', 'shift', 'cmd']:
                            time.sleep(0.1) 
                        else:
                            time.sleep(0.05) 

                    elif action['type'] == 'key_up':
                        k = self.clean_key(action['key'])
                        pyautogui.keyUp(k)
                        time.sleep(0.05)
                        
                if current_loop < loop_count - 1 and not self.stop_playback_flag:
                    self.wait_with_pause(1, current_status_text)

        except Exception as e:
            print(e)
        
        finally:
            pb_listener.stop()
            self._safe_release()
            
            msg = "Stopped by User (ESC pressed)" if self.stop_playback_flag else "Playback Finished"
            color = "orange" if self.stop_playback_flag else "green"
            
            self.root.after(0, self.indicator.stop) 
            self.root.after(0, self.root.deiconify)
            self.root.after(0, lambda: self.status_label.config(text=msg, fg=color))
            self.root.after(0, lambda: self.toggle_buttons(False))

    def _safe_release(self):
        try:
            pyautogui.mouseUp(button='left')
            pyautogui.mouseUp(button='right')
            pyautogui.mouseUp(button='middle')
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('shift')
            pyautogui.keyUp('alt')
        except: pass

    def clean_key(self, k):
        if k in ["ctrl_l", "ctrl_r"]: return "ctrl"
        if k in ["alt_l", "alt_r"]: return "alt"
        if k in ["shift_l", "shift_r"]: return "shift"
        return k

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroRecorderApp(root)
    root.mainloop()