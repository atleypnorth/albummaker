import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from pathlib import Path
import logging
import webbrowser
import paramiko

from maker import AlbumMaker, _logger as maker_logger
from config import AlbumMakerConfig

_logger = logging.getLogger(__name__)

big_font = ("Times New Roman", 15)
body_font = ("Times New Roman", 10)


class GUILoggingHandler(logging.Handler):
    """Put log messages into a Text widget
    """

    def __init__(self, text_area, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_area = text_area

    def emit(self, record):
        self.text_area.insert(tk.END, record.getMessage() + '\n')
        self.text_area.see(tk.END)
        self.text_area.update()


class ConfigDialog(tk.Toplevel):

    def __init__(self, parent, album_config):

        super().__init__(parent)
        self.transient(parent)
        self.parent = parent
        self.album_config = album_config

        row_number = 0
        ttk.Label(self, text="Configuration", font=big_font).grid(row=row_number, column=0, columnspan=3,
                                                                  sticky=tk.W + tk.E)

        # Directory select
        row_number += 2
        ttk.Label(self, text="Local album directory", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        self.folder = tk.StringVar(value=self.album_config.local_dir)
        self.folder.set(self.album_config.local_dir)
        ttk.Entry(self, textvariable=self.folder).grid(column=1, row=row_number, sticky=tk.W + tk.E)
        find_dir = ttk.Button(self, text="...", command=self.get_folder)
        find_dir.grid(column=2, row=row_number)

        # Number per page
        row_number += 2
        self.number_per_page = tk.IntVar(value=self.album_config.per_page)
        ttk.Label(self, text="Number per page", font=body_font). \
            grid(column=0, row=row_number, sticky=tk.W)
        ttk.Spinbox(self, textvariable=self.number_per_page, from_=8, to=30).grid(column=1, row=row_number)

        # Image size
        row_number += 2
        self.image_size_x = tk.IntVar(value=self.album_config.image_size[0])
        self.image_size_y = tk.IntVar(value=self.album_config.image_size[1])
        ttk.Label(self, text="Image size", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        ttk.Spinbox(self, textvariable=self.image_size_x, from_=200, to=1000, increment=5, width=8). \
            grid(column=1, row=row_number, sticky=tk.W)
        ttk.Label(self, text=" x ", font=body_font).grid(column=1, row=row_number)
        ttk.Spinbox(self, textvariable=self.image_size_y, from_=200, to=1000, increment=5, width=8). \
            grid(column=1, row=row_number, sticky=tk.E)

        # Thumbnail size
        row_number += 2
        self.thumb_size_x = tk.IntVar(value=self.album_config.thumbnail_size[0])
        self.thumb_size_y = tk.IntVar(value=self.album_config.thumbnail_size[1])
        ttk.Label(self, text="Thumbnail size", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        ttk.Spinbox(self, textvariable=self.thumb_size_x, from_=200, to=1000, increment=5, width=8). \
            grid(column=1, row=row_number, sticky=tk.W)
        ttk.Label(self, text=" x ", font=body_font).grid(column=1, row=row_number)
        ttk.Spinbox(self, textvariable=self.thumb_size_y, from_=200, to=1000, increment=5, width=8). \
            grid(column=1, row=row_number, sticky=tk.E)

        # List of 'who'
        row_number += 2
        ttk.Label(self, text="Who (one per line)", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        row_number += 1
        self.who_text = tk.Text(self, font=body_font, height=5)
        self.who_text.grid(column=0, columnspan=3, row=row_number, sticky=tk.E + tk.W)
        self.who_text.insert(tk.INSERT, '\n'.join(self.album_config.who))
        row_number += 2

        # Upload details
        row_number += 2
        ttk.Label(self, text="Upload details", font=big_font).grid(row=row_number, column=0, columnspan=3,
                                                                   sticky=tk.W + tk.E)
        row_number += 2
        ttk.Label(self, text="Server", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        self.server = tk.StringVar(value=self.album_config.target_server)
        ttk.Entry(self, textvariable=self.server).grid(column=1, row=row_number, sticky=tk.W + tk.E, columnspan=2)
        row_number += 2
        ttk.Label(self, text="Directory", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        self.directory = tk.StringVar(value=self.album_config.target_directory)
        ttk.Entry(self, textvariable=self.directory).grid(column=1, row=row_number, sticky=tk.W + tk.E, columnspan=2)
        row_number += 2
        ttk.Label(self, text="Username", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        self.username = tk.StringVar(value=self.album_config.target_username)
        ttk.Entry(self, textvariable=self.username).grid(column=1, row=row_number, sticky=tk.W + tk.E, columnspan=2)
        row_number += 2
        ttk.Label(self, text="Password", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        self.password = tk.StringVar(value=self.album_config.target_password)
        ttk.Entry(self, textvariable=self.password, show='*'). \
            grid(column=1, row=row_number, sticky=tk.W + tk.E, columnspan=2)
        row_number += 2
        ttk.Label(self, text="URL", font=body_font).grid(column=0, row=row_number, sticky=tk.W)
        self.url = tk.StringVar(value=self.album_config.target_url)
        ttk.Entry(self, textvariable=self.url).grid(column=1, row=row_number, sticky=tk.W + tk.E, columnspan=2)

        # Buttons
        row_number += 2
        self.cancel = ttk.Button(self, text='Cancel', command=self.destroy)
        self.cancel.grid(column=1, row=row_number, sticky=tk.W)
        self.ok = ttk.Button(self, text='OK', command=self._save_config)
        self.ok.grid(column=1, row=row_number, sticky=tk.E)

        self.pack()

    def get_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.folder.get())
        if folder_selected:
            self.folder.set(folder_selected)

    def _save_config(self):
        self.album_config.local_dir = self.folder.get()
        self.album_config.per_page = self.number_per_page.get()
        self.album_config.image_size = [self.image_size_x.get(), self.image_size_y.get()]
        self.album_config.thumbnail_size = [self.thumb_size_x.get(), self.thumb_size_y.get()]

        _logger.info('Checking remote details')
        with paramiko.Transport((self.server.get(), self.album_config.target_port)) as transport:
            transport.connect(username=self.username.get(), password=self.password.get())
            with paramiko.SFTPClient.from_transport(transport) as sftp:
                sftp.stat(self.directory.get())

        self.album_config.target_server = self.server.get()
        self.album_config.target_directory = self.directory.get()
        self.album_config.target_username = self.username.get()
        self.album_config.target_password = self.password.get()
        self.album_config.target_url = self.url.get()
        self.album_config.save()
        self.destroy()


class AlbumMakerGUI(tk.Frame):
    """
    """

    def __init__(self, master=None, config_file=None):
        super().__init__(master)
        self.master = master
        self.album_config = AlbumMakerConfig(config_file)
        self.who_values = self.album_config.who
        self.create_widgets()
        self.pack()
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        maker_logger.setLevel(logging.INFO)
        handler = GUILoggingHandler(self.output)
        handler.setFormatter(log_formatter)
        maker_logger.addHandler(handler)

    def create_widgets(self):
        self.title_frame = ttk.Label(self, text='Album Maker', font=big_font).grid(row=0, column=0, sticky='EW',
                                                                                   columnspan=3)

        # Who select
        ttk.Label(self, text="Select who the album is for ", font=body_font).grid(column=0, row=2, sticky='W')
        self.who_choice = ttk.Combobox(self, width=20, values=self.who_values, state='readonly')
        self.who_choice.grid(column=1, row=2, sticky='W')
        self.who_choice.bind("<<ComboboxSelected>>", self.who_selected)

        # Directory select
        ttk.Label(self, text="Directory to upload", font=body_font).grid(column=0, row=3, sticky='W')
        self.folder = tk.StringVar()
        ttk.Entry(self, textvariable=self.folder).grid(column=1, row=3, sticky='EW')
        find_dir = ttk.Button(self, text="...", command=self.get_folder)
        find_dir.grid(column=2, row=3)

        # Log output
        ybar = tk.Scrollbar(self)
        self.output = tk.Text(self, font=body_font)
        self.output.grid(column=0, row=5, columnspan=3)
        ybar.config(command=self.output.yview)
        self.output.config(yscrollcommand=ybar.set)
        ybar.grid(column=3, row=5, sticky="NS")

        # Options
        self.launch_browser = tk.IntVar(value=1)
        self.browser = ttk.Checkbutton(self, text="Launch browser on generate and upload", variable=self.launch_browser)
        self.browser.grid(column=0, row=9, sticky='W')

        # Command buttons
        self.generate = ttk.Button(self, text='Generate', command=self.generate, state='disabled')
        self.generate.grid(column=0, row=10, sticky='W')
        self.upload = ttk.Button(self, text='Upload', command=self.upload, state='disabled')
        self.upload.grid(column=0, row=10, sticky='E')
        self.config_btn = ttk.Button(self, text='Config', command=self.create_config_window)
        self.config_btn.grid(column=1, row=10, sticky='E')
        self.quit = ttk.Button(self, text='Quit', command=self.master.destroy)
        self.quit.grid(column=2, row=10, sticky='E')

    def create_config_window(self):
        """
        """
        d = ConfigDialog(self, self.album_config)
        self.wait_window(d)

    def get_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            if folder_selected != self.folder.get():
                self.output.delete(1.0, tk.END)
            self.folder.set(folder_selected)
            if self.who_choice.current() is not None:
                self.generate['state'] = 'normal'
            else:
                self.generate['state'] = 'disabled'

    def who_selected(self, event):
        self.output.delete(1.0, tk.END)
        if self.folder.get():
            self.generate['state'] = 'normal'
        else:
            self.generate['state'] = 'disabled'

    def generate(self):
        self.output.insert(tk.END, '======== Generating\n')
        self.output.see(tk.END)
        try:
            self.config(cursor="wait")
            self.update()
            maker = AlbumMaker()
            maker.configure(None, self.folder.get(), None, self.who_values[self.who_choice.current()].lower())
            maker.generate()
            if self.launch_browser.get():
                url = maker.output_dir / Path('index.html')
                webbrowser.open(url, new=2)
            self.output.insert(tk.END, '======== Done generating\n')
            self.upload['state'] = 'normal'
        except Exception as e:
            self.output.insert(tk.END, '======== FAILED: ' + str(e) + '\n')
        finally:
            self.config(cursor="")
            self.update()
            self.output.see(tk.END)

    def upload(self):
        self.output.insert(tk.END, '======== Uploading\n')
        self.output.see(tk.END)
        try:
            self.config(cursor="wait")
            self.update()
            maker = AlbumMaker()
            maker.configure(None, self.folder.get(), None, self.who_values[self.who_choice.current()].lower())
            url = maker.upload()
            self.output.insert(tk.END, '======== Done upload\n')
            if self.launch_browser.get():
                webbrowser.open(url, new=2)
        except Exception as e:
            self.output.insert(tk.END, '======== FAILED: ' + str(e) + '\n')
        finally:
            self.config(cursor="")
            self.update()
            self.output.see(tk.END)


if __name__ == '__main__':
    root = tk.Tk()
    app = AlbumMakerGUI(master=root)
    root.title("Album Maker")
    root.geometry("800x500")
    app.mainloop()
