import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from maker import AlbumMaker, _logger as maker_logger
from pathlib import Path
import logging
import yaml


class GUILoggingHandler(logging.Handler):
    """
    """

    def __init__(self, text_area, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_area = text_area

    def emit(self, record):
        self.text_area.insert(tk.END, record.getMessage() + '\n')
        self.text_area.see(tk.END)
        self.text_area.update()


class AlbumMakerGUI(tk.Frame):

    def __init__(self, master=None, config_file=None):
        super().__init__(master)
        self.master = master
        self.pack()
        if config_file is None:
            config_file = Path(__file__).parents[0] / Path('config.yml')
        with open(config_file) as infile:
            self.album_config = yaml.safe_load(infile)
        self.who_values = self.album_config['who']
        self.create_widgets()
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        maker_logger.setLevel(logging.INFO)
        handler = GUILoggingHandler(self.output)
        handler.setFormatter(log_formatter)
        maker_logger.addHandler(handler)

    def create_widgets(self):
        big_font = ("Times New Roman", 15)
        body_font = ("Times New Roman", 10)
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

        # Command buttons
        self.generate = ttk.Button(self, text='Generate', command=self.generate, state='disabled')
        self.generate.grid(column=0, row=10)
        self.upload = ttk.Button(self, text='Upload', command=self.upload, state='disabled')
        self.upload.grid(column=1, row=10)
        self.quit = ttk.Button(self, text='Quit', command=self.master.destroy)
        self.quit.grid(column=2, row=10)

    def get_folder(self):
        folder_selected = filedialog.askdirectory()
        self.folder.set(folder_selected)
        if self.who_choice.current() is not None:
            self.generate['state'] = 'normal'
        else:
            self.generate['state'] = 'disabled'

    def who_selected(self, event):
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
            maker.upload()
            self.output.insert(tk.END, '======== Done upload\n')
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
