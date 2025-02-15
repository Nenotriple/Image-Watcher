#region - Imports

# First-party
import tkinter as tk
from tkinter import ttk, messagebox

# Custom
from scalable_image_label import ScalableImageLabel

# Third-party
from TkToolTip.TkToolTip import TkToolTip as ToolTip


# UI padding
PAD = 2

# Tooltips
TIP_PADX = 5
TIP_PADY = 15
TIP_DELAY = 500
TIP_WRAP = 250


#endregion
#region - GUI Setup


class ImageWatcherGUI:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.image_label = None
        self.navigation_bindings = []
        self.last_index = 0


    def setup_gui(self):
        # Main Frame
        frame = ttk.Frame(self.root, padding=PAD)
        frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.create_control_frame(frame)
        self.create_image_label(frame)
        self.create_bottom_frame(frame)
        self.setup_bindings()


    def create_control_frame(self, frame):
        control_frame = ttk.Frame(frame)
        self.control_frame = control_frame
        control_frame.grid(row=0, column=0, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        # Configure columns
        control_frame.grid_columnconfigure(0, weight=1)  # prev button
        control_frame.grid_columnconfigure(1, weight=1)  # next button
        control_frame.grid_columnconfigure(2, weight=0)  # count frame
        control_frame.grid_columnconfigure(3, weight=0)  # quick switch
        control_frame.grid_columnconfigure(4, weight=0)  # options
        # Prev button
        self.prev_button = ttk.Button(control_frame, text="Prev", command=lambda: self.parent.navigate("prev"))
        self.prev_button.grid(row=0, column=0, padx=PAD, sticky="ew")
        # Next button
        self.next_button = ttk.Button(control_frame, text="Next", command=lambda: self.parent.navigate("next"))
        self.next_button.grid(row=0, column=1, padx=PAD, sticky="ew")
        # Index count/entry
        self.create_index_count(control_frame)
        # Quick switch button
        self.quick_switch_button = ttk.Button(control_frame, text="!", width=1, takefocus=False, command=self.on_status_flag_click)
        self.quick_switch_button.grid(row=0, column=3, sticky="ns", padx=1)
        self.quick_switch_tooltip = ToolTip(self.quick_switch_button, "...", padx=TIP_PADX, pady=TIP_PADY)
        # Options menu
        self.create_control_options_menu(control_frame)


    def create_index_count(self, control_frame):
        count_frame = ttk.Frame(control_frame)
        count_frame.grid(row=0, column=2, padx=PAD)
        # Current index entry
        self.current_index_entry = ttk.Entry(count_frame, width=5, justify='right')
        self.current_index_entry.pack(side='left')
        # Total count label
        ttk.Label(count_frame, text="/").pack(side='left')
        self.total_count_label = ttk.Label(count_frame, text="0")
        self.total_count_label.pack(side='left')


    def create_control_options_menu(self, control_frame):
        options_button = ttk.Menubutton(control_frame, text="☰")
        options_button.grid(row=0, column=4, padx=PAD)
        self.options_menu = tk.Menu(options_button, tearoff=0)
        options_button['menu'] = self.options_menu
        # File menu
        self.file_menu = tk.Menu(self.options_menu, tearoff=0)
        self.options_menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Change Folder...", command=self.parent.change_folder)
        self.file_menu.add_command(label="Refresh Image Index", command=self.parent.refresh_index)
        self.file_menu.add_command(label="Refresh Metadata Database", command=self.parent.database_manager.update_database)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Open Current Folder", command=self.parent.file_manager.show_in_explorer)
        self.file_menu.add_command(label="Open Current Saved Folder", command=self.parent.file_manager.open_saved_folder)
        self.file_menu.add_command(label="Open Current Image", command=self.parent.file_manager.open_image)
        # Edit menu
        self.edit_menu = tk.Menu(self.options_menu, tearoff=0)
        self.options_menu.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Delete Current Image", accelerator="Del", command=self.parent.delete_image)
        self.edit_menu.add_command(label="Move Current Image to Saved", accelerator="Ins", command=self.parent.move_image_to_saved_folder)
        self.edit_menu.add_command(label="Export Current Image Metadata", command=self.parent.export_current_image_metadata)
        self.edit_menu.add_command(label="Export ALL Image Metadata", command=self.parent.export_all_metadata)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Move All...", command=self.parent.move_all_images)
        self.edit_menu.add_command(label="Move Current Image...", command=self.parent.move_image_to)
        self.edit_menu.add_command(label="Copy Current Image...", command=self.parent.copy_image_to)
        self.edit_menu.add_separator()
        self.edit_menu.add_checkbutton(label="Toggle: Quick Move", variable=self.parent.quick_move_var)
        self.edit_menu.add_checkbutton(label="Toggle: Quick Delete", variable=self.parent.quick_delete_var)
        # View menu
        self.view_menu = tk.Menu(self.options_menu, tearoff=0)
        self.options_menu.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_checkbutton(label="Toggle: Live Mode", variable=self.parent.live_check_var, command=self.parent.toggle_live_updates)
        self.view_menu.add_checkbutton(label="Toggle: Command Row", variable=self.parent.show_command_row_var, command=self.toggle_command_row)
        self.view_menu.add_checkbutton(label="Toggle: Always On Top", variable=self.parent.always_on_top_var, command=self.toggle_always_on_top)
        self.view_menu.add_separator()
        self.view_menu.add_radiobutton(label="Image Mode: Fill", variable=self.parent.image_scale_mode_var, value="fill", command=lambda: self.image_label.set_scale_mode('fill'))
        self.view_menu.add_radiobutton(label="Image Mode: Center", variable=self.parent.image_scale_mode_var, value="center", command=lambda: self.image_label.set_scale_mode('center'))
        self.view_menu.add_separator()
        self.view_menu.add_checkbutton(label="Swap Image/Stats", variable=self.parent.image_paned_window_swap_var, command=self.configure_image_paned_window)
        self.view_menu.add_checkbutton(label="Swap Horizontal/Vertical", variable=self.parent.image_paned_window_horizontal_var, command=self.configure_image_paned_window)
        self.view_menu.add_checkbutton(label="Swap Nav Row Top/Bottom", variable=self.parent.swap_nav_row_var, command=self.swap_nav_row)
        # About menu
        self.options_menu.add_command(label="About", command=self.show_about_dialog)


    def create_image_label(self, frame):
        # Create a PanedWindow
        self.image_paned_window = tk.PanedWindow(frame, orient="horizontal", sashwidth=6, bg="#d0d0d0", bd=0)
        self.image_paned_window.grid(row=1, column=0, sticky="nsew")
        frame.grid_rowconfigure(1, weight=1)
        # Image Pane
        image_pane = ttk.Frame(self.image_paned_window)
        image_pane.grid_rowconfigure(0, weight=1)
        image_pane.grid_columnconfigure(0, weight=1)
        self.image_label = ScalableImageLabel(image_pane)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        self.image_paned_window.add(image_pane, stretch="always", minsize=100)
        # Stats Pane
        self.stats_pane = ttk.Frame(self.image_paned_window)
        self.stats_pane.grid_rowconfigure(0, weight=1)
        self.stats_pane.grid_columnconfigure(0, weight=1)
        self.image_paned_window.add(self.stats_pane, stretch="never", width=300)
        self.create_image_context_menu()


    def create_image_context_menu(self):
        self.image_context_menu = tk.Menu(self.root, tearoff=0)
        self.image_context_menu.add_command(label="Open Image", command=self.parent.file_manager.open_image)
        self.image_context_menu.add_command(label="Show in File Explorer", command=self.parent.file_manager.show_in_explorer)
        self.image_context_menu.add_command(label="Export Image Metadata...", command=self.parent.export_current_image_metadata)
        self.image_context_menu.add_separator()
        self.image_context_menu.add_command(label="Delete", accelerator="Del", command=self.parent.delete_image)
        self.image_context_menu.add_command(label="Save", accelerator="Ins", command=self.parent.move_image_to_saved_folder)
        self.image_context_menu.add_separator()
        self.image_context_menu.add_command(label="Move To...", command=self.parent.move_image_to)
        self.image_context_menu.add_command(label="Copy To...", command=self.parent.copy_image_to)
        self.image_context_menu.add_separator()
        self.image_context_menu.add_radiobutton(label="Image Mode: Fill", variable=self.parent.image_scale_mode_var, value="fill", command=lambda: self.image_label.set_scale_mode('fill'))
        self.image_context_menu.add_radiobutton(label="Image Mode: Center", variable=self.parent.image_scale_mode_var, value="center", command=lambda: self.image_label.set_scale_mode('center'))


    def create_bottom_frame(self, frame):
        self.bottom_frame = ttk.Frame(frame)
        self.bottom_frame.grid(row=2, column=0, sticky="nsew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_rowconfigure(1, weight=1)
        self.create_command_buttons()
        self.create_stats_frame()


    def create_command_buttons(self):
        self.command_frame = ttk.LabelFrame(self.bottom_frame, text="Commands")
        self.command_frame.grid(row=0, column=0, sticky="ew")
        button_frame = ttk.Frame(self.command_frame)
        button_frame.pack(side="top", fill="x")
        # Delete
        delete_btn = ttk.Button(button_frame, width=5, text="Delete", command=self.parent.delete_image)
        delete_btn.pack(side="left", padx=PAD, pady=PAD, expand=True, fill="x")
        ToolTip(delete_btn, "Delete the current image", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)
        # Save
        save_btn = ttk.Button(button_frame, width=5, text="Save", command=self.parent.move_image_to_saved_folder)
        save_btn.pack(side="left", padx=PAD, pady=PAD, expand=True, fill="x")
        ToolTip(save_btn, "Move the current image to the 'Saved Images' folder", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)
        # Open
        open_btn = ttk.Button(button_frame, width=5, text="Open", command=self.parent.file_manager.open_image)
        open_btn.pack(side="left", padx=PAD, pady=PAD, expand=True, fill="x")
        ToolTip(open_btn, "Open the current image in the default image viewer", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)
        # Filter frame
        filter_frame = ttk.Frame(self.command_frame)
        filter_frame.pack(side="top", fill="x")
        # Filter label
        filter_label = ttk.Label(filter_frame, text="Filter:")
        filter_label.pack(side="left", padx=PAD, pady=PAD)
        # Filter entry
        self.filter_entry = ttk.Entry(filter_frame, width=10)
        self.filter_entry.pack(side="left", padx=PAD, pady=PAD, expand=True, fill="x")
        ToolTip(self.filter_entry, "Filter images based on the selected parameters and input text.\n\nSupports Operators:\n'space' (AND), ~ (OR), - (NOT)\nWrap text in parenthesis to treat as a single term.", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)
        # Filter menu
        self.create_filter_menu(filter_frame)
        # Filter Clear
        filter_clear_btn = ttk.Button(filter_frame, text="Clear", command=self.parent.reset_filters)
        filter_clear_btn.pack(side="left", padx=PAD, pady=PAD)
        ToolTip(filter_clear_btn, "Clear the current filter", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)
        # Refresh DB
        refresh_db_btn = ttk.Button(filter_frame, text="Refresh", command=self.parent.database_manager.update_database)
        refresh_db_btn.pack(side="left", padx=PAD, pady=PAD)
        ToolTip(refresh_db_btn, "Refresh the image database and load new file changes from the selected directory", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)
        # Help button
        help_btn = ttk.Button(filter_frame, text="?", width=1, command=self.show_filter_help)
        help_btn.pack(side="right", padx=PAD, pady=PAD)
        ToolTip(help_btn, "Show filter help and advanced syntax", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)


    def create_filter_menu(self, filter_frame):
        self.filter_type_menu = ttk.Menubutton(filter_frame, text="Search")
        self.filter_type_menu.pack(side="left", padx=PAD, pady=PAD)
        ToolTip(self.filter_type_menu, "Select an image parameter to search in", padx=TIP_PADX, pady=TIP_PADY, delay=TIP_DELAY, wraplength=TIP_WRAP)
        filter_type_menu = tk.Menu(self.filter_type_menu, tearoff=0)
        self.filter_type_menu['menu'] = filter_type_menu
        # Add ALL option
        filter_type_menu.add_checkbutton(label="ALL", variable=self.parent.filter_states["ALL"], command=lambda: self.parent.handle_all_filter())
        filter_type_menu.add_separator()
        # Add prompt-related options
        prompt_options = ["Positive Prompt", "Negative Prompt"]
        for option in prompt_options:
            filter_type_menu.add_checkbutton(label=option, variable=self.parent.filter_states[option], command=lambda opt=option: self.parent.handle_filter_type_change(opt))
        filter_type_menu.add_separator()
        # Add parameter options
        param_options = ["Steps", "Sampler", "Schedule type", "CFG scale", "Size", "Model"]
        for option in param_options:
            filter_type_menu.add_checkbutton(label=option, variable=self.parent.filter_states[option], command=lambda opt=option: self.parent.handle_filter_type_change(opt))


    def create_stats_frame(self):
        self.stats_frame = ttk.LabelFrame(self.stats_pane, text="Image Stats")
        self.stats_frame.grid(row=0, column=0, sticky="nsew")
        self.stats_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_rowconfigure(1, weight=1)
        # Header frame for label and options
        stat_sub_frame = ttk.Frame(self.stats_frame)
        stat_sub_frame.grid(row=0, column=0, sticky="nsew")
        stat_sub_frame.grid_columnconfigure(0, weight=1)
        # Label
        self.stats_label = ttk.Label(stat_sub_frame, text="", justify="left")
        self.stats_label.grid(row=0, column=0, padx=PAD, pady=PAD, sticky="w")
        # Stats Text
        text_frame = ttk.Frame(self.stats_frame)
        text_frame.grid(row=1, column=0, padx=PAD, pady=PAD, sticky="nsew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        # Text widget with scrollbar
        self.stats_text = tk.Text(text_frame, wrap="word", height=10, width=5)
        self.stats_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.stats_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.stats_text.configure(yscrollcommand=scrollbar.set)


#endregion
#region - Bindings and Events


    def setup_bindings(self):
        # Store bindings for later management
        self.navigation_bindings = [
            (self.root, '<Left>', lambda e: self.parent.navigate("prev")),
            (self.root, '<Right>', lambda e: self.parent.navigate("next"))
        ]
        # Apply nav bindings
        self.apply_navigation_bindings()
        # Add non-navigation bindings
        self.root.bind('<Delete>', lambda e: self.parent.delete_image())
        self.root.bind('<Insert>', lambda e: self.parent.move_image_to_saved_folder())
        # Index entry
        self.current_index_entry.bind('<Return>', self.on_index_entry)
        # Image Label
        self.image_label.bind('<Button-1>', self.start_move, add='+')
        self.image_label.bind('<Button-1>', lambda e: self.image_label.focus_set(), add='+')
        self.image_label.bind('<B1-Motion>', self.on_move)
        self.image_label.bind('<Button-3>', self.show_image_context_menu)
        self.image_label.bind('<MouseWheel>', self.wheel_navigate)
        # Filter Entry
        self.filter_entry.bind('<Return>', lambda e: self.parent.apply_filters())
        self.filter_entry.bind('<FocusIn>', self.on_filter_entry_focus)
        self.filter_entry.bind('<FocusOut>', self.on_filter_entry_focus_out)


    def apply_navigation_bindings(self):
        for widget, key, callback in self.navigation_bindings:
            widget.bind(key, callback)


    def remove_navigation_bindings(self):
        for widget, key, _ in self.navigation_bindings:
            widget.unbind(key)


    def on_filter_entry_focus(self, event):
        self.remove_navigation_bindings()


    def on_filter_entry_focus_out(self, event):
        self.apply_navigation_bindings()


#endregion
#region - GUI Logic


    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.parent.always_on_top_var.get())


    def check_bottom_frame_visibility(self):
        if not self.parent.show_command_row_var.get():
            self.bottom_frame.grid_remove()
        else:
            self.bottom_frame.grid()


    def toggle_command_row(self):
        if self.parent.show_command_row_var.get():
            self.command_frame.grid()
        else:
            self.command_frame.grid_remove()
        self.check_bottom_frame_visibility()


    def toggle_stats(self):
        if self.parent.show_stats_var.get():
            self.stats_frame.grid()
            self.parent.update_image_stats()
        else:
            self.stats_frame.grid_remove()
        self.check_bottom_frame_visibility()


    def show_image_context_menu(self, event):
        if self.parent.image_manager and self.parent.image_manager.get_current_image():
            self.image_context_menu.tk_popup(event.x_root, event.y_root)


    def update_count_label(self):
        if self.parent.image_manager:
            total = len(self.parent.image_manager.image_files)
            current = self.parent.image_manager.current_index + 1 if total > 0 else 0
            pad_length = len(str(total))
            self.current_index_entry.delete(0, tk.END)
            self.current_index_entry.insert(0, f"{current:0{pad_length}d}")
            self.total_count_label.config(text=str(total))


    def configure_image_paned_window(self):
        # Handle pane orientation
        orientation = "vertical" if self.parent.image_paned_window_horizontal_var.get() else "horizontal"
        self.image_paned_window.configure(orient=orientation)
        # Remove existing panes
        for pane in self.image_paned_window.panes():
            self.image_paned_window.forget(pane)
        # Re-add panes in the correct order based on swap variable
        if self.parent.image_paned_window_swap_var.get():
            self.image_paned_window.add(self.stats_pane, stretch="never")
            self.image_paned_window.add(self.image_label.master, stretch="always", minsize=100)
        else:
            self.image_paned_window.add(self.image_label.master, stretch="always", minsize=100)
            self.image_paned_window.add(self.stats_pane, stretch="never")


    def on_index_entry(self, event):
        try:
            index = int(self.current_index_entry.get()) - 1  # Convert to 0-based index
            if self.parent.image_manager:
                if self.parent.image_manager.set_index(index):
                    self.parent.navigate(index=index)
                else:
                    self.update_count_label()  # Reset to current value if invalid
        except ValueError:
            self.update_count_label()  # Reset to current value if invalid input


    def show_filter_help(self):
        help_text = self.parent.help_text.FILTER_HELP_TEXT
        messagebox.showinfo("Filter Help", help_text)


    def show_about_dialog(self):
        about_text = self.parent.help_text.ABOUT_TEXT
        messagebox.showinfo("About", about_text)


    def swap_nav_row(self):
        self.control_frame.grid_forget()
        self.image_paned_window.grid_forget()
        self.bottom_frame.grid_forget()
        root = self.control_frame.master
        if self.parent.swap_nav_row_var.get():
            self.image_paned_window.grid(row=0, column=0, sticky="nsew")
            root.grid_rowconfigure(0, weight=1)
            self.control_frame.grid(row=1, column=0, sticky="ew")
            root.grid_rowconfigure(1, weight=0)
            self.bottom_frame.grid(row=2, column=0, sticky="nsew")
            root.grid_rowconfigure(2, weight=0)
        else:
            self.control_frame.grid(row=0, column=0, sticky="ew")
            root.grid_rowconfigure(0, weight=0)
            self.image_paned_window.grid(row=1, column=0, sticky="nsew")
            root.grid_rowconfigure(1, weight=1)
            self.bottom_frame.grid(row=2, column=0, sticky="nsew")
            root.grid_rowconfigure(2, weight=0)


#endregion
#region - Navigation


    def wheel_navigate(self, event):
        if not self.parent.image_manager:
            return
        if event.delta < 0:
            self.parent.navigate("next")
        else:
            self.parent.navigate("prev")


    def on_status_flag_click(self):
        if not self.parent.image_manager or not self.parent.image_manager.image_files:
            return

        if self.parent.image_manager.current_index == 0:
            # We're at index 0, try to return to last position
            if self.parent.image_manager.recall_position():
                self.quick_switch_button['text'] = "⤸"
                self.parent.navigate(index=self.parent.image_manager.current_index)
        else:
            # Store current position and go to index 0
            self.parent.image_manager.remember_position()
            self.quick_switch_button['text'] = "⤹"
            self.parent.navigate(index=0)


#endregion
#region - Window Dragging


    def start_move(self, event):
        self.parent._drag_data["x"] = event.x
        self.parent._drag_data["y"] = event.y


    def on_move(self, event):
        delta_x = event.x - self.parent._drag_data["x"]
        delta_y = event.y - self.parent._drag_data["y"]
        x = self.root.winfo_x() + delta_x
        y = self.root.winfo_y() + delta_y
        self.root.geometry(f"+{x}+{y}")


#endregion
