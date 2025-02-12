#region - Imports


# First-party
import tkinter as tk

# Third-party
from PIL import Image, ImageTk


#endregion
#region - ScalableImageLabel


class ScalableImageLabel(tk.Label):
    """
    A custom tkinter Label widget that displays an image with scaling capabilities.

    This widget automatically handles image resizing when the window is resized,
    with options to maintain aspect ratio or stretch to fill the available space.

    Attributes:
        original_image (PIL.Image): The source image in its original size
        displayed_image (ImageTk.PhotoImage): The currently displayed image
        keep_aspect (bool): Whether to maintain the image's aspect ratio when scaling
        scaling_method (str): The scaling method to use ('nearest', 'bilinear', 'bicubic', or 'lanczos')
    """


    SCALING_METHODS = {
        'nearest': Image.NEAREST,
        'bilinear': Image.BILINEAR,
        'bicubic': Image.BICUBIC,
        'lanczos': Image.LANCZOS
    }


    def __init__(self, master=None, image_path="", keep_aspect=False, width=None, height=None, scaling_method='lanczos', *args, **kwargs):
        """
        Initialize the ScalableImageLabel widget.

        Args:
            master: Parent widget
            image_path (str): Path to the image file
            keep_aspect (bool): Whether to maintain aspect ratio when scaling
            width (int, optional): Initial width of the widget
            height (int, optional): Initial height of the widget
            scaling_method (str): The scaling method to use ('nearest', 'bilinear', 'bicubic', or 'lanczos')
        """
        super().__init__(master, *args, **kwargs)
        self.scaling_method = self._validate_scaling_method(scaling_method)
        self.displayed_image = None
        self.original_image = None
        self.keep_aspect = keep_aspect
        self.resize_timer = None
        self.last_resize_time = 0
        self.image_path = ""

        # Bind resize event first
        self.bind("<Configure>", self._resize, add="+")
        # Set initial size if specified
        if width is not None and height is not None:
            self.config(width=width, height=height)
        # Load image if provided
        if image_path:
            self.update_image(image_path)


    def _validate_scaling_method(self, method):
        """
        Validate and return the PIL scaling method constant.

        Args:
            method (str): The scaling method name

        Returns:
            int: PIL scaling method constant

        Raises:
            ValueError: If the scaling method is not supported
        """
        method = method.lower()
        if method not in self.SCALING_METHODS:
            raise ValueError(f"Unsupported scaling method: {method}. Choose from {', '.join(self.SCALING_METHODS.keys())}")
        return self.SCALING_METHODS[method]


    def update_image(self, image_path):
        """
        Update the displayed image with a new image file.

        Args:
            image_path (str): Path to the new image file
        """
        self.image_path = image_path
        self.original_image = Image.open(image_path)
        if self.winfo_width() > 1 and self.winfo_height() > 1:
            self._final_resize(self.winfo_width(), self.winfo_height())
        else:
            self._final_resize(self.original_image.width, self.original_image.height)


    def _configure_initial_size(self, width, height):
        """Configure the initial size of the widget and display the image."""
        if not self.original_image:  # Skip if no image is loaded
            return
        if width is not None or height is not None:
            # Calculate dimensions based on specified width/height
            new_width, new_height = self._calculate_dimensions(width, height, *self.original_image.size)
            self.config(width=new_width, height=new_height)
            self._resize_image(new_width, new_height)
        else:
            # Use original image dimensions
            self.config(width=self.original_image.width, height=self.original_image.height)


    def _calculate_dimensions(self, target_width, target_height, orig_width, orig_height):
        """
        Calculate new dimensions based on target size and aspect ratio settings.

        Args:
            target_width (int): Desired width
            target_height (int): Desired height
            orig_width (int): Original image width
            orig_height (int): Original image height

        Returns:
            tuple: New width and height
        """
        if self.keep_aspect:
            # Calculate scaling ratio based on available dimensions
            if target_width is not None and target_height is not None:
                ratio = max(target_width / orig_width, target_height / orig_height)
            elif target_width is not None:
                ratio = target_width / orig_width
            else:
                ratio = target_height / orig_height
            new_width = int(orig_width * ratio)
            new_height = int(orig_height * ratio)
        else:
            new_width = target_width if target_width is not None else orig_width
            new_height = target_height if target_height is not None else orig_height
        return new_width, new_height


    def _resize_image(self, width, height, force_quality=False):
        """
        Resize the image to the specified dimensions.

        Args:
            width (int): Target width
            height (int): Target height
            force_quality (bool): Force using the high-quality scaling method
        """
        if not self.original_image:  # Skip if no image is loaded
            return
        if width <= 0 or height <= 0:
            return
        if self.keep_aspect:
            orig_width, orig_height = self.original_image.size
            ratio = min(width / orig_width, height / orig_height)
            new_width = int(orig_width * ratio)
            new_height = int(orig_height * ratio)
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            # Use NEAREST during active resize, original scaling method when resize ends
            current_method = self.scaling_method if force_quality else Image.NEAREST
            resized = self.original_image.resize((new_width, new_height), current_method)
        else:
            current_method = self.scaling_method if force_quality else Image.NEAREST
            resized = self.original_image.resize((width, height), current_method)
        self.displayed_image = ImageTk.PhotoImage(resized)
        self.config(image=self.displayed_image)


    def _resize(self, event):
        """Handle resize events by updating the image size."""
        if not self.original_image:  # Skip if no image is loaded
            return
        # Cancel any pending high-quality resize
        if self.resize_timer is not None:
            self.after_cancel(self.resize_timer)
        # Perform fast resize immediately
        self._resize_image(event.width, event.height, force_quality=False)
        # Schedule high-quality resize for 200ms after last resize event
        self.resize_timer = self.after(200, lambda: self._final_resize(event.width, event.height))


    def _final_resize(self, width, height):
        """Perform final high-quality resize after resizing stops."""
        self.resize_timer = None
        self._resize_image(width, height, force_quality=True)


    def get_image_path(self):
        """
        Get the current image path.

        Returns:
            str: The path of the currently displayed image, or empty string if no image is loaded.
        """
        return self.image_path


    def clear(self):
        """
        Clear the displayed image and reset internal image references.
        This effectively resets the widget to its initial empty state.
        """
        self.image_path = ""
        self.original_image = None
        self.displayed_image = None
        self.config(image='')


#endregion
#region - Example Usage

#def main():
#    root = tk.Tk()
#    root.title("Scalable Image Label Example")
#
#    # Create a ScalableImageLabel widget (You can also create it without an image)
#    image_label = ScalableImageLabel(root,image_path="image.png", keep_aspect=True, width=200, scaling_method='lanczos')
#    image_label.pack(fill=tk.BOTH, expand=True)
#
#    image_label.bind("<Button-1>", lambda e: image_label.update_image("image2.png"))
#    root.mainloop()
#
#if __name__ == "__main__":
#    main()


#endregion
