#region - Imports

# First-party
import os
import time
import shlex
import tkinter as tk
from tkinter import filedialog

# Local
from interface_manager import ImageWatcherGUI
from image_manager import ImageManager
from image_database_manager import DatabaseManager
from watchdog_manager import WatchdogManager
from file_manager import FileManager
import help_text


#endregion
#region - Constants


TITLE = "Image Watcher"
INITIAL_WINDOW_SIZE = "800x750"
MIN_WINDOW_SIZE = "200x150"

VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tif', '.tiff')
SAVED_FOLDER_NAME = "Saved Images"
IMAGE_DB_FILENAME = "IW_database.json"


#endregion
#region - ImageWatcher


class ImageWatcher:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()

        self.observer = None
        self.image_manager = None
        self.database_manager = None
        self.watchdog_manager = None
        self.watch_folder_path = None
        self.current_image_path = None
        self._drag_data = {"x": 0, "y": 0}
        self.last_known_file_count = 0
        self.last_index = 0

        self.live_check_var = tk.BooleanVar(value=True)
        self.show_stats_var = tk.BooleanVar(value=True)
        self.quick_move_var = tk.BooleanVar(value=False)
        self.quick_delete_var = tk.BooleanVar(value=False)
        self.swap_nav_row_var = tk.BooleanVar(value=False)
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.text_stat_size_var = tk.StringVar(value="Medium")
        self.show_command_row_var = tk.BooleanVar(value=True)
        self.image_paned_window_swap_var = tk.BooleanVar(value=False)
        self.image_paned_window_horizontal = tk.BooleanVar(value=True)

        self.filter_states = {
            "ALL": tk.BooleanVar(value=True),
            "Positive Prompt": tk.BooleanVar(value=True),
            "Negative Prompt": tk.BooleanVar(value=True),
            "Steps": tk.BooleanVar(value=True),
            "Sampler": tk.BooleanVar(value=True),
            "Schedule type": tk.BooleanVar(value=True),
            "CFG scale": tk.BooleanVar(value=True),
            "Size": tk.BooleanVar(value=True),
            "Model": tk.BooleanVar(value=True)
        }

        self.previous_live_state = None
        self.file_manager = None
        self.filter_active = False


    def setup_window(self):
        self.root.title(TITLE)
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # Get window width and height from INITIAL_WINDOW_SIZE
        window_width, window_height = map(int, INITIAL_WINDOW_SIZE.split('x'))
        # Calculate center position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        # Set the window's position and size
        self.root.geometry(f"{INITIAL_WINDOW_SIZE}+{x}+{y}")
        self.root.minsize(*map(int, MIN_WINDOW_SIZE.split('x')))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


    def run(self):
        self.watch_folder_path = filedialog.askdirectory(title="Select Folder to Watch")
        if not self.watch_folder_path:
            self.root.destroy()
            return
        self.help_text = help_text
        self.image_manager = ImageManager(self.watch_folder_path, VALID_EXTENSIONS)
        self.database_manager = DatabaseManager(self.root, self.watch_folder_path, VALID_EXTENSIONS, IMAGE_DB_FILENAME)
        self.file_manager = FileManager(self.watch_folder_path, self.image_manager, SAVED_FOLDER_NAME)
        self.gui = ImageWatcherGUI(self.root, self)
        self.gui.setup_gui()
        self.file_manager.initialize_gui_in_filemanager(self.gui)
        self.setup_watchdog()
        self.database_manager.update_database()
        self.update_display()
        self.root.focus_force()
        self.root.mainloop()


    def on_closing(self):
        if self.watchdog_manager:
            self.watchdog_manager.stop()
        self.root.destroy()


#endregion
#region - Watchdog


    def setup_watchdog(self):
        self.watchdog_manager = WatchdogManager(self.watch_folder_path, self.schedule_update)
        self.watchdog_manager.setup_watchdog(self.live_check_var.get())


    def schedule_update(self):
        self.root.after(0, self.update_display)


    def toggle_live_updates(self):
        if self.watchdog_manager:
            self.watchdog_manager.toggle_live_updates(self.live_check_var.get())
            if self.live_check_var.get():
                self.navigate(index=0)


#endregion
#region - Navigation

    def check_file_changes(self):
        """Check if files have changed and update index if needed."""
        if not self.image_manager or not self.watch_folder_path:
            return False
        if self.filter_active:
            return False  # Skip refreshing if a filter is active
        current_files = [
            f for f in os.listdir(self.watch_folder_path)
            if f.lower().endswith(VALID_EXTENSIONS)
        ]
        if len(current_files) != len(self.image_manager.image_files):
            self.image_manager.refresh_image_list(reset_index=False)
            return True
        return False


    def navigate(self, direction="next", index=None):
        if not self.image_manager:
            return
        # Check for file changes if live mode is disabled
        if not self.live_check_var.get():
            self.check_file_changes()
        image_path = self.image_manager.navigate_images(direction, index)
        if image_path:
            self.display_image(image_path)
            self.gui.update_count_label()
            # Update quick switch button state
            if self.image_manager.current_index == 0:
                self.gui.quick_switch_button['text'] = "⤸"
                self.gui.quick_switch_tooltip.config(text="Click to return to last viewed image")
            else:
                self.gui.quick_switch_button['text'] = "⤹"
                self.gui.quick_switch_tooltip.config(text="Click to return to first image")


    def change_folder(self):
        new_folder = filedialog.askdirectory(title="Select New Folder to Watch")
        if new_folder:
            # Stop existing observer if it exists
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            # Update folder and managers
            self.watch_folder_path = new_folder
            self.image_manager = ImageManager(self.watch_folder_path, VALID_EXTENSIONS)
            # Update database manager with new path
            self.database_manager.update_watch_folder(new_folder)
            # Setup new watchdog for the new path
            self.watchdog_manager = WatchdogManager(self.watch_folder_path, self.schedule_update)
            if self.live_check_var.get():
                self.watchdog_manager.setup_watchdog(True)
            # Update database and display
            self.database_manager.update_database()
            self.update_display()
            self.watch_folder_path = new_folder


#endregion
#region - Image Display


    def display_image(self, image_path):
        try:
            self.gui.image_label.update_image(image_path)
            self.update_image_stats()
        except Exception as e:
            print("ERROR: display_image - loading image:", e)


    def update_display(self):
        if self.image_manager:
            # Store current image path and index
            current_image_path = self.image_manager.get_current_image()
            current_index = self.image_manager.current_index
            if self.live_check_var.get():
                self.refresh_index(reset_index=False)
            old_file_count = self.last_known_file_count
            self.last_index = self.image_manager.current_index
            self.apply_filters()
            new_file_count = len(self.image_manager.image_files)
            self.last_known_file_count = new_file_count
            # Reset current index if needed
            if self.image_manager.image_files:
                if self.last_index >= len(self.image_manager.image_files):
                    self.last_index = len(self.image_manager.image_files) - 1
                self.image_manager.current_index = max(self.last_index, 0)
            else:
                self.image_manager.current_index = -1
            # Check for new images and update display accordingly
            if new_file_count > old_file_count:
                if self.last_index == 0:
                    self.navigate(index=0)  # Force update to new image at index 0
                self.gui.quick_switch_button['text'] = "!"
            # Update display
            if self.current_image_path:
                # Try to maintain the current image
                if current_image_path and current_image_path in self.image_manager.image_files and current_index > 0:
                    new_index = self.image_manager.image_files.index(current_image_path)
                    self.navigate(index=new_index)
                else:
                    self.navigate(index=0)
            self.gui.update_count_label()


    def refresh_index(self, reset_index=True):
        if self.image_manager:
            self.current_image_path = self.image_manager.get_current_image()
            self.image_manager.refresh_image_list(reset_index=reset_index)
            # Check if current image is still available
            if not self.current_image_path or self.current_image_path not in self.image_manager.image_files:
                # If current image is gone, show the most recent image
                if len(self.image_manager.image_files) > 0:
                    self.navigate(index=0)
                else:
                    # No images left
                    self.gui.image_label.clear()
                    self.gui.update_count_label()


#endregion
#region - Image Stats


    def update_image_stats(self):
        if not self.show_stats_var.get() or not self.image_manager:
            return
        current_image = self.image_manager.get_current_image()
        if not current_image:
            return
        try:
            file_size = os.path.getsize(current_image)
            file_name = os.path.basename(current_image)
            image_width = self.gui.image_label.original_image.width
            image_height = self.gui.image_label.original_image.height
            mod_time = os.path.getmtime(current_image)
            mod_time_human_readable = time.strftime('%Y-%m-%d, %I:%M:%S %p', time.localtime(mod_time))
            # Basic stats
            label_stats = (
                f"File: {file_name}\n"
                f"Size: {file_size / 1024:.1f} KB\n"
                f"Dimensions: {image_width}x{image_height}\n"
                f"Modified: {mod_time_human_readable}"
            )
            self.gui.stats_label.config(text=label_stats)
            # Add PNG metadata to text widget if available
            self.gui.stats_text.config(state="normal")
            self.gui.stats_text.delete('1.0', "end")
            # Configure text tags
            self.gui.stats_text.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
            if current_image.lower().endswith('.png'):
                png_metadata = self.database_manager.extract_png_metadata(current_image)
                if png_metadata:
                    # Prompts
                    for key in ["Positive Prompt", "Negative Prompt"]:
                        if key in png_metadata:
                            if key != "Positive Prompt":
                                self.gui.stats_text.insert("end", "\n")
                            self.gui.stats_text.insert("end", f"{key}:", "bold")
                            self.gui.stats_text.insert("end", f"\n{png_metadata[key]}\n")
                            del png_metadata[key]
                    # Other parameters
                    self.gui.stats_text.insert("end", "\n")
                    self.gui.stats_text.insert("end", "Parameters:", "bold")
                    self.gui.stats_text.insert("end", "\n")
                    for key, value in png_metadata.items():
                        self.gui.stats_text.insert("end", f"{key}: ", "bold")
                        self.gui.stats_text.insert("end", f"{value}\n")
            self.gui.stats_text.config(state="disabled")
        except Exception as e:
            self.gui.stats_label.config(text=f"Error reading stats: {str(e)}")
            self.gui.stats_text.config(state="normal")
            self.gui.stats_text.delete('1.0', "end")
            self.gui.stats_text.insert('1.0', f"Error reading stats: {str(e)}")
            self.gui.stats_text.config(state="disabled")


#endregion
#region - Filtering Logic


    def apply_filters(self):
        if not self.image_manager:
            return
        # Load database and get filter text
        database = self.database_manager.load_database()
        filter_text = self.gui.filter_entry.get().strip()
        # Handle live mode based on filter state
        if filter_text.strip():
            # Store current live state and disable if active
            if self.live_check_var.get():
                self.previous_live_state = True
                self.live_check_var.set(False)
                self.gui.view_menu.entryconfig("Toggle: Live Mode", state="disable")
                self.toggle_live_updates()
        else:
            # Restore previous live state if there was one
            if self.previous_live_state:
                self.gui.view_menu.entryconfig("Toggle: Live Mode", state="normal")
                self.live_check_var.set(True)
                self.toggle_live_updates()
                self.previous_live_state = None
        # Use shlex.split to support phrases enclosed in quotes
        tokens = [token.lower() for token in shlex.split(filter_text)]
        use_or = "~" in tokens
        # Extract positive terms (ignoring the "~" tokens and negative tokens)
        positive_terms = [token for token in tokens if token != "~" and not token.startswith('-')]
        # Negative terms
        negative_terms = [token[1:] for token in tokens if token.startswith('-')]
        active_filters = [key for key, var in self.filter_states.items() if var.get() and key != "ALL"]
        # If no filter text tokens or no active filters: refresh image list and stop filtering
        if not tokens or not active_filters:
            self.filter_active = False
            self.image_manager.refresh_image_list()
            self.navigate(index=0)
            self.gui.update_count_label()
            return
        self.filter_active = True
        # Apply filters on database
        filtered_images = []
        for filepath, metadata in database.items():
            if not os.path.exists(filepath):  # Skip if file doesn't exist
                continue
            found_negative = False
            found_positive = True  # Default for AND logic
            if positive_terms:
                if use_or:
                    # For OR, image qualifies if any active filter field contains ANY positive term
                    found_positive = False
                    for filter_key in active_filters:
                        if filter_key == "Size":
                            value_str = f"{metadata.get('width', '')}x{metadata.get('height', '')}".lower()
                        else:
                            value_str = str(metadata.get(filter_key, '')).lower()
                        if any(term in value_str for term in positive_terms):
                            found_positive = True
                            break
                else:
                    # For AND, each term must be found in at least one active field
                    for term in positive_terms:
                        term_found = False
                        for filter_key in active_filters:
                            if filter_key == "Size":
                                value_str = f"{metadata.get('width', '')}x{metadata.get('height', '')}".lower()
                            else:
                                value_str = str(metadata.get(filter_key, '')).lower()
                            if term in value_str:
                                term_found = True
                                break
                        if not term_found:
                            found_positive = False
                            break
            # Check negative terms in each active filter field
            for filter_key in active_filters:
                if filter_key == "Size":
                    value_str = f"{metadata.get('width', '')}x{metadata.get('height', '')}".lower()
                else:
                    value_str = str(metadata.get(filter_key, '')).lower()
                if any(neg in value_str for neg in negative_terms):
                    found_negative = True
                    break
            if found_positive and not found_negative:
                filtered_images.append(filepath)
        # Update image manager with filtered results
        current_image = self.image_manager.get_current_image()
        self.image_manager.image_files = sorted(filtered_images, key=os.path.getmtime, reverse=True)
        # Try to maintain the current image position if it's in the filtered results
        if current_image and current_image in filtered_images:
            new_index = filtered_images.index(current_image)
            self.image_manager.current_index = new_index
        else:
            self.image_manager.current_index = 0 if filtered_images else -1
        # directly update the visible image
        if self.image_manager.current_index != -1:
            self.display_image(self.image_manager.get_current_image())
        else:
            self.gui.image_label.clear()
        self.gui.update_count_label()


    def reset_filters(self):
        self.gui.filter_entry.delete(0, "end")
        # Restore previous live state if there was one
        if self.previous_live_state:
            self.live_check_var.set(True)
            self.toggle_live_updates()
            self.previous_live_state = None
        self.apply_filters()


    def handle_all_filter(self):
        all_state = self.filter_states["ALL"].get()
        for key in self.filter_states:
            if key != "ALL":
                self.filter_states[key].set(all_state)
        self.apply_filters()


    def handle_filter_type_change(self, option):
        # If any individual filter is unchecked, uncheck ALL
        if not self.filter_states[option].get():
            self.filter_states["ALL"].set(False)
        # If all individual filters are checked, check ALL
        elif all(self.filter_states[key].get()
                for key in self.filter_states if key != "ALL"):
            self.filter_states["ALL"].set(True)
        self.apply_filters()


#endregion
#region - File Handling


    def delete_image(self):
        current_index = self.file_manager.delete_image(self.quick_delete_var.get())
        self._after_process_navigation(current_index)


    def move_image_to_saved_folder(self):
        current_index = self.file_manager.move_image_to_saved_folder(self.quick_move_var.get())
        self._after_process_navigation(current_index)


    def _after_process_navigation(self, current_index):
        if current_index is not None:
            if len(self.image_manager.image_files) > 0:
                self.apply_filters()
                self.navigate(index=current_index)
            else:
                self.gui.image_label.clear()
                self.gui.update_count_label()


    def move_all_images(self):
        if self.file_manager.move_all_images():
            self.navigate(index=0)
            self.gui.update_count_label()
            self.reset_filters()


    def move_image_to(self):
        current_index = self.file_manager.move_image_to()
        self._after_process_navigation(current_index)


    def copy_image_to(self):
        self.file_manager.copy_image_to()


#endregion
#region - Main


def main():
    app = ImageWatcher()
    app.run()


if __name__ == "__main__":
    main()


#endregion
