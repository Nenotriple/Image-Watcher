#region Imports


# Third-party
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler
from threading import Timer


#endregion
#region ImageEventHandler


class ImageEventHandler(FileSystemEventHandler):
    def __init__(self, update_callback: callable):
        super().__init__()
        self.update_callback = update_callback
        self.timer = None
        self.debounce_time = 1  # One second delay


    def on_any_event(self, event):
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(self.debounce_time, self.update_callback)
        self.timer.start()


#endregion
#region WatchdogManager


class WatchdogManager:
    def __init__(self, folder_path: str, update_callback: callable):
        self.folder_path = folder_path
        self.update_callback = update_callback
        self.observer: BaseObserver | None = None


    def setup_watchdog(self, is_active: bool = True):
        self.observer = self.create_observer()
        if is_active:
            self.observer.start()


    def create_observer(self) -> BaseObserver:
        event_handler = ImageEventHandler(self.update_callback)
        observer = Observer()
        observer.schedule(event_handler, path=self.folder_path, recursive=False)
        return observer


    def toggle_live_updates(self, is_active: bool):
        if is_active:
            if not self.observer or not self.observer.is_alive():
                self.observer = self.create_observer()
                self.observer.start()
        else:
            self.stop()


    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None


#endregion
