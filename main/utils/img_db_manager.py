#region Imports


# First-party
import os
import json
import time

# UI
import tkinter as tk
from tkinter import ttk

# Third-party
import png
from PIL import Image


#endregion
#region ProgressPopup


class ProgressPopup:
    def __init__(self, parent):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Updating Database")
        self.popup.transient(parent)
        self.popup.grab_set()
        # Center the popup
        self.popup.update_idletasks()
        width = self.popup.winfo_width()
        height = self.popup.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.popup.geometry(f"+{x}+{y}")
        # Status label
        self.status_label = tk.Label(self.popup, text="Scanning files...", pady=10)
        self.status_label.pack()
        # Detail label
        self.detail_label = tk.Label(self.popup, text="")
        self.detail_label.pack()
        # Progress bar
        self.progressbar = ttk.Progressbar(self.popup, length=250, mode='determinate')
        self.progressbar.pack(fill="x", padx=10, pady=10)
        # Percent label
        self.percent_label = tk.Label(self.popup, text="0%", anchor="e", width=10)
        self.percent_label.pack(fill="x", padx=10, pady=(0, 10))
        self.popup.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button


    def update(self, progress, status="", detail=""):
        self.progressbar['value'] = progress
        self.percent_label['text'] = f"{int(progress)}%"
        if status:
            self.status_label['text'] = status
        if detail:
            self.detail_label['text'] = detail
        self.popup.update()


    def close(self):
        self.popup.destroy()


#endregion
#region DatabaseManager



class DatabaseManager:
    def __init__(self, root, watch_folder, valid_extensions, image_db_filename):
        self.root = root
        self.watch_folder = watch_folder
        self.valid_extensions = valid_extensions
        self.database_filename = image_db_filename
        self.database_path = os.path.join(self.watch_folder, self.database_filename)
        self._cached_database = None


    #region Public API


    def update_watch_folder(self, new_folder):
        """Update the watch folder and reset database cache."""
        self.watch_folder = new_folder
        self.database_path = os.path.join(self.watch_folder, self.database_filename)
        self._cached_database = None


    def get_entry(self, image_path):
        """Get the database entry for a given image filepath. Returns None if not found."""
        return self.load_database().get(image_path)


    def add_entry(self, image_path):
        """Add a single new entry to the database and save."""
        database = self.load_database()
        if image_path in database:
            return False
        metadata = self._get_image_metadata(image_path)
        if metadata is None:
            return False
        database[image_path] = metadata
        self.save_database(database)
        return True


    def remove_entry(self, image_path):
        """Remove a single entry from the database and save."""
        database = self.load_database()
        if image_path in database:
            del database[image_path]
            self.save_database(database)
            return True
        return False


    def update_database(self, recursive=False):
        """Creates or updates the database of images and their metadata."""
        if not self.root:
            return super().update_database(recursive)
        database = self.load_database()
        current_files = set()
        progress_popup = ProgressPopup(self.root)
        all_files, total_files = self._collect_valid_files(recursive)
        self._sync_files_with_database(database, current_files, progress_popup, all_files, total_files)
        progress_popup.update(100, "Cleaning up database...", "")
        self._cleanup_removed_files(database, current_files)
        self.save_database(database)
        progress_popup.close()
        return database


    #endregion
    #region Database IO


    def load_database(self):
        """Load the image database from JSON file."""
        if self._cached_database is None:
            try:
                with open(self.database_path, 'r', encoding="utf-8") as f:
                    self._cached_database = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self._cached_database = {}
        return self._cached_database


    def save_database(self, database):
        """Save the image database to JSON file."""
        with open(self.database_path, 'w', encoding="utf-8") as f:
            json.dump(database, f, indent=4)
        self._cached_database = database


    def _delete_database(self):
        """Delete the database file if it exists."""
        if os.path.exists(self.database_path):
            os.remove(self.database_path)


    #endregion
    #region File Collection & Sync


    def _collect_valid_files(self, recursive):
        walk_iter = os.walk(self.watch_folder) if recursive else [(self.watch_folder, [], os.listdir(self.watch_folder))]
        all_files = [os.path.join(root, file)
                     for root, _, files in walk_iter
                     for file in files if file.lower().endswith(self.valid_extensions)]
        return all_files, len(all_files)


    def _sync_files_with_database(self, database, current_files, progress_popup, all_files, total_files):
        if not all_files:
            self._delete_database()
            progress_popup.update(100, "No images found, database deleted", "")
            return
        for i, file_path in enumerate(all_files, 1):
            current_files.add(file_path)
            progress = (i / total_files) * 100
            status = f"Processing file {i} of {total_files}"
            detail = os.path.basename(file_path)
            progress_popup.update(progress, status, detail)
            if self._should_process_file(file_path, database):
                metadata = self._get_image_metadata(file_path)
                if metadata is not None:
                    database[file_path] = metadata


    def _should_process_file(self, file_path, database):
        """Determine if a file needs to be processed based on modification time."""
        if file_path not in database:
            return True
        last_modified = os.path.getmtime(file_path)
        return database[file_path].get('modified_time_stamp') != last_modified


    def _cleanup_removed_files(self, database, current_files):
        """Remove database entries for files that no longer exist."""
        removed_files = set(database.keys()) - current_files
        for file_path in removed_files:
            del database[file_path]


    #endregion
    #region Metadata Extraction


    def _get_image_metadata(self, file_path):
        """Extract all metadata for an image file, including PNG-specific if needed."""
        try:
            with Image.open(file_path) as image:
                metadata = self._extract_basic_metadata(file_path, image)
                if file_path.lower().endswith('.png'):
                    png_metadata = self.extract_png_metadata(file_path)
                    if png_metadata:
                        metadata.update(png_metadata)
                return metadata
        except Exception as e:
            print(f"ERROR: _get_image_metadata - processing {file_path}: {e}")
            return None


    def _extract_basic_metadata(self, file_path, image):
        """Extract basic metadata common to all image types."""
        return {
            "file_size": os.path.getsize(file_path),
            "width": image.size[0],
            "height": image.size[1],
            "format": image.format,
            "modified_time": time.strftime('%Y-%m-%d, %I:%M:%S %p', time.localtime(os.path.getmtime(file_path))),
            "modified_time_stamp": os.path.getmtime(file_path)
        }


    def extract_png_metadata(self, filepath):
        """Extract metadata from PNG chunks and format SD parameters."""
        if not self._is_valid_png(filepath):
            return None
        chunks = self._get_png_chunks(filepath)
        if not chunks:
            return None
        metadata = {}
        for chunk_type, chunk_data in chunks:
            if chunk_type == b'tEXt':
                key, value = self._process_text_chunk(chunk_data)
                if key and value:
                    if key == "parameters":
                        metadata.update(self._parse_parameters(value))
                    else:
                        metadata[key] = value
        return metadata


    def _is_valid_png(self, filepath):
        return filepath.lower().endswith('.png')


    def _get_png_chunks(self, filepath):
        try:
            png_reader = png.Reader(filepath)
            return png_reader.chunks()
        except Exception as e:
            print(f"ERROR: _get_png_chunks - reading PNG chunks: {e}")
            return None


    def _process_text_chunk(self, chunk_data):
        try:
            key, value = chunk_data.split(b'\0', 1)
            return key.decode('latin-1'), value.decode('latin-1')
        except Exception:
            return None, None


    def _parse_parameters(self, params_text):
        metadata = {}
        parts = params_text.split('\n', 2)
        metadata["Positive Prompt"] = parts[0] if len(parts) > 0 else ""
        if len(parts) > 1:
            neg_prompt = parts[1].replace("Negative prompt:", "").strip()
            metadata["Negative Prompt"] = neg_prompt
        if len(parts) > 2:
            params = parts[2].strip()
            for param in params.split(", "):
                if ":" in param:
                    k, v = param.split(":", 1)
                    metadata[k.strip()] = v.strip()
                else:
                    metadata[f"Param_{len(metadata)}"] = param
        return metadata

    #endregion


#endregion
#region Load/Save database


    def load_database(self):
        """Load the image database from JSON file"""
        if self._cached_database is None:
            try:
                with open(self.database_path, 'r', encoding="utf-8") as f:
                    self._cached_database = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self._cached_database = {}
        return self._cached_database


    def save_database(self, database):
        """Save the image database to JSON file"""
        with open(self.database_path, 'w', encoding="utf-8") as f:
            json.dump(database, f, indent=4)
        self._cached_database = database  # Update the cached database


#endregion
#region Extract metadata


    def extract_png_metadata(self, filepath):
        """Extract metadata from PNG chunks and format SD parameters"""
        if not self._is_valid_png(filepath):
            return None
        # Extract PNG chunks
        chunks = self._get_png_chunks(filepath)
        if not chunks:
            return None
        # Process text chunks
        metadata = {}
        for chunk_type, chunk_data in chunks:
            if (chunk_type == b'tEXt'):
                key, value = self._process_text_chunk(chunk_data)
                if key and value:
                    if key == "parameters":
                        metadata.update(self._parse_parameters(value))
                    else:
                        metadata[key] = value
        return metadata


    def _is_valid_png(self, filepath):
        """Check if the file is a valid PNG"""
        return filepath.lower().endswith('.png')


    def _get_png_chunks(self, filepath):
        """Extract raw chunks from PNG file"""
        try:
            png_reader = png.Reader(filepath)
            return png_reader.chunks()
        except Exception as e:
            print(f"ERROR: _get_png_chunks - reading PNG chunks: {e}")
            return None


    def _process_text_chunk(self, chunk_data):
        """Process a single text chunk and return key-value pair"""
        try:
            key, value = chunk_data.split(b'\0', 1)
            return key.decode('latin-1'), value.decode('latin-1')
        except:
            return None, None


    def _parse_parameters(self, params_text):
        """Parse parameters text into structured metadata"""
        metadata = {}
        parts = params_text.split('\n', 2)
        # Handle positive prompt
        metadata["Positive Prompt"] = parts[0] if len(parts) > 0 else ""
        # Handle negative prompt
        if len(parts) > 1:
            neg_prompt = parts[1].replace("Negative prompt:", "").strip()
            metadata["Negative Prompt"] = neg_prompt
        # Handle additional parameters
        if len(parts) > 2:
            params = parts[2].strip()
            for param in params.split(", "):
                if ":" in param:
                    k, v = param.split(":", 1)
                    metadata[k.strip()] = v.strip()
                else:
                    metadata[f"Param_{len(metadata)}"] = param
        return metadata


#endregion
#region Update database


    def update_database(self, recursive=False):
        """Creates or updates the database of images and their metadata"""
        if not self.root:
            return super().update_database(recursive)
        database = self.load_database()
        current_files = set()
        # Create progress popup
        progress_popup = ProgressPopup(self.root)
        # Collect all valid files first
        all_files, total_files = self._collect_valid_files(recursive)
        self._sync_files_with_database(database, current_files, progress_popup, all_files, total_files)
        progress_popup.update(100, "Cleaning up database...", "")
        self._cleanup_removed_files(database, current_files)
        self.save_database(database)
        progress_popup.close()
        return database


    def _collect_valid_files(self, recursive):
        walk_iter = os.walk(self.watch_folder) if recursive else [(self.watch_folder, [], os.listdir(self.watch_folder))]
        all_files = []
        for root, _, files in walk_iter:
            for file in files:
                if file.lower().endswith(self.valid_extensions):
                    all_files.append(os.path.join(root, file))
        total_files = len(all_files)
        return all_files,total_files


    def _delete_database(self):
        """Delete the database file if it exists"""
        if os.path.exists(self.database_path):
            os.remove(self.database_path)


    def _sync_files_with_database(self, database, current_files, progress_popup, all_files, total_files):
        if not all_files:
            # If no valid images exist, delete the database and return
            self._delete_database()
            progress_popup.update(100, "No images found, database deleted", "")
            return
        # Process each file
        for i, file_path in enumerate(all_files, 1):
            current_files.add(file_path)
            # Update progress
            progress = (i / total_files) * 100
            status = f"Processing file {i} of {total_files}"
            detail = os.path.basename(file_path)
            progress_popup.update(progress, status, detail)
            # Process file if necessary
            if self._should_process_file(file_path, database):
                self._process_single_file(file_path, database)


    def _should_process_file(self, file_path, database):
        """Determine if a file needs to be processed based on modification time"""
        if file_path not in database:
            return True
        last_modified = os.path.getmtime(file_path)
        return database[file_path].get('modified_time_stamp') != last_modified


    def _process_single_file(self, file_path, database):
        """Process a single image file and update its metadata in the database"""
        try:
            with Image.open(file_path) as image:
                metadata = self._extract_basic_metadata(file_path, image)
                if file_path.lower().endswith('.png'):
                    png_metadata = self.extract_png_metadata(file_path)
                    if png_metadata:
                        metadata.update(png_metadata)
                database[file_path] = metadata
        except Exception as e:
            print(f"ERROR: _process_single_file - processing {file_path}: {e}")


    def _extract_basic_metadata(self, file_path, image):
        """Extract basic metadata common to all image types"""
        return {
            "file_size": os.path.getsize(file_path),
            "width": image.size[0],
            "height": image.size[1],
            "format": image.format,
            "modified_time": time.strftime('%Y-%m-%d, %I:%M:%S %p', time.localtime(os.path.getmtime(file_path))),
            "modified_time_stamp": os.path.getmtime(file_path)
        }


    def _cleanup_removed_files(self, database, current_files):
        """Remove database entries for files that no longer exist"""
        removed_files = set(database.keys()) - current_files
        for file_path in removed_files:
            del database[file_path]


#endregion
