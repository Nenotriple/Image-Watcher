#region - Imports


# First-party
import os


#endregion
#region - ImageManager


class ImageManager:
    def __init__(self, folder, extensions):
        self.folder = folder
        self.valied_extensions = extensions
        self.image_files = []
        self.current_index = -1
        self.current_image_path = None
        self._last_position = 0
        self.refresh_image_list()


    def refresh_image_list(self, reset_index=True):
        """Refresh the list of images in the watched folder."""
        current_path = self.get_current_image()
        self.image_files = [
            os.path.join(self.folder, f) for f in os.listdir(self.folder)
            if f.lower().endswith(self.valied_extensions)
        ]
        self.image_files.sort(key=os.path.getmtime, reverse=True)
        if not self.image_files:
            self.current_index = -1
            return
        if reset_index:
            if current_path and current_path in self.image_files:
                self.current_index = self.image_files.index(current_path)
            else:
                self.current_index = 0
        else:
            # Maintain position but ensure it's valid
            self.current_index = min(self.current_index, len(self.image_files) - 1)
            self.current_index = max(0, self.current_index)


    def get_current_image(self):
        """Return the current image path."""
        return self.image_files[self.current_index] if self.current_index >= 0 else None


    def get_latest_image(self):
        """Return the most recently modified image in the folder."""
        return self.image_files[0] if self.image_files else None


    def remember_position(self):
        """Store current position for later recall."""
        self._last_position = self.current_index


    def recall_position(self):
        """Return to last remembered position."""
        if 0 <= self._last_position < len(self.image_files):
            self.current_index = self._last_position
            return True
        return False


    def set_index(self, index):
        """Safely set the current index."""
        if not self.image_files:
            self.current_index = -1
            return False
        if 0 <= index < len(self.image_files):
            self.current_index = index
            return True
        return False


    def navigate_images(self, direction="next", index=None):
        """Navigate through images with improved index management."""
        if not self.image_files:
            return None
        if index is not None:
            if self.set_index(index):
                return self.get_current_image()
            return None
        if direction == "next":
            self.current_index = (self.current_index + 1) % len(self.image_files)
        elif direction == "prev":
            self.current_index = (self.current_index - 1) % len(self.image_files)

        return self.get_current_image()


#endregion
