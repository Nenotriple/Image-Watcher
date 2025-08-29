"""
Quick Info:

"help_text" can be a dictionary, list, or string.
  - If "help_text" is a dictionary, it's expected to contain header-content pairs.
  - If "help_text" is not a dictionary and "text_format" is "rich", it's treated as plain text.

"rich" text formatting:
  - Headers (keys) are displayed larger and bold.
  - Content (values) are displayed as normal text.
  - Wrap content in double asterisks (**) for bold text.
  - Wrap content in single asterisks (*) for italic text.
  - Wrap content in single backticks (`) for code formatting (monospace font, highlighted background).

Other Features:
  - The help window can be centered relative to its master window.
  - An author label is displayed at the bottom of the window.
  - Pressing Escape or closing the window hides it (does not destroy).

General Use:
  - Create a HelpWindow instance, passing the Tkinter 'Tk.()' object (root).
  - Call "open_window" with the desired title, geometry, help text, and format.
  - Call "close_window" to hide the window.
"""


#region - Imports


# Standard GUI
import tkinter as tk
from tkinter import scrolledtext

from . import help_text


#endregion
#region - HelpWindow


AUTHOR = "Created by: github.com/Nenotriple"


class HelpWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("Help")
        self.minsize(200, 200)
        self.geometry("400x700")
        self.bind("<Escape>", self.close_window)
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self._setup_widgets()
        self.withdraw()


#endregion
#region - Window Methods


    def open_window(self, title=None, text=None, geometry=None, format="rich"):
        """Opens and displays the help window with specified settings.

        This method configures and shows the help window, updating its title,
        geometry, and content as specified. The window is centered relative
        to its master window and brought to the front.

        Args:
            title (str, optional): Window title. If None, no change.
            text (Union[str, Dict[str, str], List[str]], optional): Content to display.
                Can be a dictionary ("rich"), plain text, or a list. ("simple")
            geometry (str, optional): Window geometry in format "WxH" or "WxH+X+Y".
                If None, no change.
            format (str, optional): Format for displaying text. Options are:
                - "rich": Uses styled formatting for headers and allows bold/italic text (default).
                - "simple": Displays plain text without formatting.
        """
        self._update_window(title, geometry)
        self._update_help_text(text, format)
        self.deiconify()
        self._center_window()
        self.lift()


    def close_window(self, event=None):
        """Closes the help window and hides it from view."""
        self.withdraw()


    def _update_window(self, title=None, geometry=None):
        """Updates the help window's title and geometry."""
        if title is not None:
            self.title(title)
        if geometry is not None:
            self.geometry(geometry)


    def _center_window(self):
        """Centers the help window relative to its master window."""
        if not self.master:
            return
        self.update_idletasks()
        # Get master's geometry
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        # Get current help window size
        help_width = self.winfo_width()
        help_height = self.winfo_height()
        # Ensure the help window does not exceed the master's dimensions
        target_width = min(help_width, master_width)
        target_height = min(help_height, master_height)
        # Calculate centered position within master
        x = master_x + (master_width - target_width) // 2
        y = master_y + (master_height - target_height) // 2
        # Update geometry with the new dimensions and position
        self.geometry(f"{target_width}x{target_height}+{x}+{y}")


#endregion
#region - Create Interface


    def _setup_widgets(self):
        self._create_textbox()
        self._create_footer_label()


    def _create_textbox(self):
        self.textbox = scrolledtext.ScrolledText(self, wrap="word", height=1)
        self.textbox.pack(expand=True, fill='both')
        self.textbox.tag_config("#header",   font=("", 18, "bold"), justify='center')
        self.textbox.tag_config("##header",  font=("", 12, "bold"))
        self.textbox.tag_config("bold",      font=("", 10, "bold"))
        self.textbox.tag_config("italic",    font=("", 10, "italic"))
        self.textbox.tag_config("content",   font=("", 10))
        try:
            # Prefer monospace font
            self.textbox.tag_config("code", font=("Consolas", 10), background="#f3f3f3")
        except Exception:
            self.textbox.tag_config("code", background="#f3f3f3")


    def _create_footer_label(self):
        tk.Label(self, text=AUTHOR, font=("", 10)).pack(side="bottom", fill="x")


#endregion
#region - Update Text


    def _update_help_text(self, help_text=None, text_format="rich"):
        """Display help text in the textbox using either simple or rich formatting.

        :param help_text: The text or dictionary to display.
        :param text_format: Determines how the text is formatted ("rich" or "simple").
        """
        self.textbox.config(state='normal')
        self.textbox.delete("1.0", "end")
        if help_text is None:
            self.textbox.insert("end", "No help text available")
            self.textbox.config(state='disabled')
            return
        if text_format == "rich" and isinstance(help_text, dict):
            self._insert_rich_text(help_text)
        else: # "simple" or not a dict
            self._insert_simple_text(help_text)
        self.textbox.config(state='disabled')


    def _insert_simple_text(self, help_text):
        """Insert the provided help text as plain text into the textbox.

        :param help_text: Can be a dict, list, or string. Each element or line is inserted as-is.
        """
        try:
            text = ""
            if isinstance(help_text, dict):
                for header, content in help_text.items():
                    text += f"{header}\n{content}\n\n"
            elif isinstance(help_text, list):
                for item in help_text:
                    text += f"{str(item)}\n"
            else:
                text = str(help_text)
            self.textbox.insert("end", text)
        except Exception as e:
            self.textbox.insert("end", f"Error: {str(e)}")


    def _insert_rich_text(self, help_text):
        """Insert the provided help text using styled headers and formatting.

        :param help_text: Expects a dict of header-content pairs for rich formatting.
        """
        try:
            for idx, (header, content) in enumerate(help_text.items()):
                tag = "#header" if idx == 0 else "##header"
                self.textbox.insert("end", header + "\n", tag)
                # Use split('\n') to preserve empty lines (consecutive newlines)
                for line in str(content).split('\n'):
                    # If the line is empty, insert a blank line to preserve spacing
                    if line == "":
                        self.textbox.insert("end", "\n")
                        continue
                    formatted_parts = self._process_text_formatting(line)
                    for tag, text in formatted_parts:
                        self.textbox.insert("end", text, tag)
                    self.textbox.insert("end", "\n")
                self.textbox.insert("end", "\n")
        except AttributeError:
            self._insert_simple_text(help_text)


    def _process_text_formatting(self, text):
        """Process text for bold, italic, and backtick code formatting.

        Recognizes the following inline markers:
        - **bold**  (double asterisks)
        - *italic*  (single asterisk)
        - `code`    (single backticks) -> preserved whitespace, uses 'code' tag
        """
        result = []
        current_pos = 0
        length = len(text)
        while current_pos < length:
            # Find next marker positions
            double_start = text.find('**', current_pos)
            single_start = text.find('*', current_pos)
            backtick_start = text.find('`', current_pos)
            # If no markers found, append the rest as content
            if double_start == -1 and single_start == -1 and backtick_start == -1:
                result.append(('content', text[current_pos:]))
                break
            # Build list of candidate markers with their positions
            candidates = []
            if double_start != -1:
                candidates.append((double_start, '**'))
            if single_start != -1:
                candidates.append((single_start, '*'))
            if backtick_start != -1:
                candidates.append((backtick_start, '`'))
            # Pick the earliest marker
            earliest_pos, earliest_mark = min(candidates, key=lambda x: x[0])
            # If there's leading plain content before the marker, append it
            if current_pos < earliest_pos:
                result.append(('content', text[current_pos:earliest_pos]))
            # Handle markers
            if earliest_mark == '**':
                double_end = text.find('**', earliest_pos + 2)
                if double_end != -1:
                    result.append(('bold', text[earliest_pos + 2:double_end]))
                    current_pos = double_end + 2
                    continue
                else:
                    # No closing marker, treat as content
                    result.append(('content', text[earliest_pos:]))
                    break
            if earliest_mark == '*':
                next_single = text.find('*', earliest_pos + 1)
                if next_single != -1:
                    result.append(('italic', text[earliest_pos + 1:next_single]))
                    current_pos = next_single + 1
                    continue
                else:
                    result.append(('content', text[earliest_pos:]))
                    break
            if earliest_mark == '`':
                bt_end = text.find('`', earliest_pos + 1)
                if bt_end != -1:
                    # Preserve exact inner text (including spaces)
                    result.append(('code', text[earliest_pos + 1:bt_end]))
                    current_pos = bt_end + 1
                    continue
                else:
                    result.append(('content', text[earliest_pos:]))
                    break
        return result
