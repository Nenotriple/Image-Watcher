#region - Imports

# First-party
import os
import shutil
import subprocess
from tkinter import messagebox, filedialog


#endregion
#region - FileManager


class FileManager:
    def __init__(self, watch_folder_path, image_manager, saved_folder_name="Saved Images"):
        self.watch_folder_path = watch_folder_path
        self.image_manager = image_manager
        self.saved_folder_name = saved_folder_name


    def initialize_gui_in_filemanager(self, gui):
        self.gui = gui


#endregion
#region - Helper Functions


    def _perform_file_operation(self, source_path, target_folder, operation):
        try:
            new_path = self._get_unique_path(source_path, target_folder)
            operation(source_path, new_path)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not perform operation: {str(e)}")
            return False


    def _get_unique_path(self, source_path, target_folder):
        filename = os.path.basename(source_path)
        new_path = os.path.join(target_folder, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(target_folder, f"{base}_{counter}{ext}")
            counter += 1
        return new_path


    def _get_unique_filename(self, filepath):
        # Generate a unique filename if one already exists
        base, ext = os.path.splitext(filepath)
        counter = 1
        unique_path = filepath
        while os.path.exists(unique_path):
            unique_path = f"{base}_{counter}{ext}"
            counter += 1
        return unique_path


#endregion
#region - File Operations


    def open_image(self):
        current_image = self.gui.image_label.get_image_path()
        if current_image:
            os.startfile(current_image)


    def show_in_explorer(self):
        current_image = self.gui.image_label.get_image_path()
        if current_image:
            subprocess.run(['explorer', '/select,', os.path.normpath(current_image)])


    def open_saved_folder(self):
        saved_folder = os.path.join(self.watch_folder_path, self.saved_folder_name)
        if os.path.exists(saved_folder):
            os.startfile(saved_folder)
        else:
            messagebox.showinfo("Info", "No saved images folder found.")


    def delete_image(self, quick_delete=False):
        current_image = self.gui.image_label.get_image_path()
        if not current_image:
            return None
        if not quick_delete and not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this image?"):
            return None

        try:
            current_index = self.image_manager.current_index
            os.remove(current_image)
            self.image_manager.refresh_image_list(reset_index=False)
            return current_index
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete image: {str(e)}")
            return None


    def move_image_to_saved_folder(self, quick_move=False):
        if not self.image_manager or not self.gui.image_label.get_image_path():
            return None
        if not quick_move:
            if not messagebox.askyesno("Confirm Move", "Are you sure you want to move this image?"):
                return None
        current_image = self.gui.image_label.get_image_path()
        saved_folder = os.path.join(self.watch_folder_path, self.saved_folder_name)
        if not os.path.exists(saved_folder):
            os.makedirs(saved_folder)
        # Move the image to the saved folder
        try:
            current_index = self.image_manager.current_index
            new_path = self._get_unique_path(current_image, saved_folder)
            os.rename(current_image, new_path)
            self.image_manager.refresh_image_list(reset_index=False)
            return current_index
        except Exception as e:
            messagebox.showerror("Error", f"Could not move image: {str(e)}")
            return None


    def move_all_images(self):
        if not self.image_manager or not self.image_manager.image_files:
            messagebox.showinfo("Info", "No images to move.")
            return
        messagebox.askokcancel("Move All Images", "This will move all images listed in the index, respecting filters.\n\nPlease select a folder to move the images to.")
        target_folder = filedialog.askdirectory(title="Select Folder to Move Images To")
        if not target_folder:
            return
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        # Move each image to the target folder
        moved_count = 0
        for image_path in self.image_manager.image_files:
            success = self._perform_file_operation(image_path, target_folder, os.rename)
            if success:
                moved_count += 1
        # Refresh the image list
        if moved_count > 0:
            self.image_manager.refresh_image_list(reset_index=False)
            if messagebox.askyesno("Success", f"Successfully moved {moved_count} images to:\n{target_folder}\n\nWould you like to open this folder?"):
                os.startfile(target_folder)
        return True


    def move_image_to(self):
        current_image = self.gui.image_label.get_image_path()
        if not current_image:
            messagebox.showinfo("Info", "No image selected.")
            return
        target_folder = filedialog.askdirectory(title="Select Folder to Move Image To")
        if not target_folder:
            return
        current_index = self.image_manager.current_index
        success = self._perform_file_operation(current_image, target_folder, os.rename)
        if success:
            messagebox.showinfo("Success", f"Moved image to:\n{target_folder}")
            self.image_manager.refresh_image_list(reset_index=False)
            return current_index
        return None


    def copy_image_to(self):
        current_image = self.gui.image_label.get_image_path()
        if not current_image:
            messagebox.showinfo("Info", "No image selected.")
            return
        target_folder = filedialog.askdirectory(title="Select Folder to Copy Image To")
        if not target_folder:
            return
        self._perform_file_operation(current_image, target_folder, shutil.copy2)
        messagebox.showinfo("Success", f"Copied image to:\n{target_folder}")


#endregion
#region - Metadata


    def format_metadata(self, metadata):
        # Format metadata as key: value on each line
        lines = []
        for key, value in metadata.items():
            lines.append(f"{key}:\n{value}\n")
        return "\n".join(lines)


    def export_current_image_metadata(self, database_manager):
        """Export formatted PNG metadata of the currently displayed image."""
        current_image = self.gui.image_label.get_image_path()
        if not current_image:
            messagebox.showinfo("Info", "No current image to export.")
            return
        metadata = database_manager.extract_png_metadata(current_image)
        if not metadata:
            messagebox.showinfo("Info", "No PNG metadata found for the current image.")
            return
        formatted = self.format_metadata(metadata)
        default_filename = os.path.splitext(os.path.basename(current_image))[0] + ".txt"
        output_file = filedialog.asksaveasfilename(title="Export Metadata", defaultextension=".txt", initialfile=default_filename, filetypes=[("Text Files", "*.txt")])
        if not output_file:
            return
        if os.path.exists(output_file):
            output_file = self._get_unique_filename(output_file)
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted)
            messagebox.showinfo("Success", f"Metadata exported to:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export metadata: {str(e)}")


    def export_all_metadata(self, database_manager):
        """Batch export formatted PNG metadata for all images in the current list."""
        if not self.image_manager.image_files:
            messagebox.showinfo("Info", "No images to export.")
            return
        target_folder = filedialog.askdirectory(title="Select Folder to Export Metadata")
        if not target_folder:
            return
        exported_count = 0
        for image_path in self.image_manager.image_files:
            metadata = database_manager.extract_png_metadata(image_path)
            if not metadata:
                continue
            formatted = self.format_metadata(metadata)
            base_filename = os.path.splitext(os.path.basename(image_path))[0] + ".txt"
            output_file = os.path.join(target_folder, base_filename)
            output_file = self._get_unique_filename(output_file)
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(formatted)
                exported_count += 1
            except Exception:
                # Skip files that cannot be written
                pass
        messagebox.showinfo("Export Completed", f"Metadata exported for {exported_count} image(s) into:\n{target_folder}")
