from pathlib import Path
from argparse import ArgumentParser
import yaml
import logging
from jinja2 import FileSystemLoader, Environment
import shutil
from PIL import Image
import base64
import paramiko

_logger = logging.getLogger()


class AlbumMaker:

    def __init__(self, config_file, input_dir, output_dir, title):
        """
        :param config_file: Yaml file with settings, if None will look for config.yml in this directory
        :param title: If none will default to directory name of input
        """
        if config_file is None:
            config_file = Path(__file__).parents[0] / Path('config.yml')
        with open(config_file) as infile:
            self.config = yaml.safe_load(infile)
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.image_dir = self.output_dir / Path('images')
        self.image_dir.mkdir(exist_ok=True)
        self.thumb_dir = self.output_dir / Path('thumbs')
        self.thumb_dir.mkdir(exist_ok=True)

        self.image_suffix = self.config.get('image_suffix', ['.jpg'])
        self.other_suffix = self.config.get('other_suffix', ['.pdf', '.mov'])

        self.per_page = self.config.get('per_page', 12)
        self.style = self.config.get('style', 'default')
        if title is None:
            self.title = self.input_dir.name

        self.template_dir = Path(__file__).parents[0] / Path('styles') / Path(self.style)
        self.environ = Environment(loader=FileSystemLoader(self.template_dir))
        self.thumbnail_size = self.config.get('thumbnail_size', [240, 240])
        self.image_size = self.config.get('image_size', [500, 500])

    def scan_input_dir(self):
        """Scan input dir for files
        """
        self.files = []
        for file in self.input_dir.glob('*'):
            file_suffix = file.suffix.lower()
            if file_suffix in self.image_suffix:
                _logger.info(f"Adding {file}")
                self.files.append((file, 'image'))
            elif file_suffix in self.other_suffix:
                _logger.info(f"Adding {file}")
                self.files.append((file, 'other'))

    def make_image(self, file, entry, workdir):
        """Make page for an image
        """
        template = self.environ.get_template('image.tmpl')
        output = Path(workdir) / Path('images') / Path(f"{file.stem}.html")
        with Image.open(file) as im:
            im.thumbnail(self.thumbnail_size)
            thumbfile = self.thumb_dir / Path(file.name)
            im.save(thumbfile)
            entry['thumb_width'] = im.width
            entry['thumb_height'] = im.height
        with Image.open(file) as im:
            im.thumbnail(self.image_size)
            resized_file = self.image_dir / Path(file.name)
            im.save(resized_file)
            entry['image_width'] = im.width
            entry['image_height'] = im.height
        entry['image_file'] = file.name
        with output.open('w') as outfile:
            template.stream(entry=entry, title=self.title).dump(outfile)
        entry['thumb'] = f"thumbs/{file.name}"

    def _write_page(self, workdir, entries, page_number, is_last_page):
        """
        :param workdir: directory for output
        :param entries: list of image entries to process
        :param page_number: current page number
        :param is_last_page: True when this is the last page
        :return: filename generated
        """
        template = self.environ.get_template('index.tmpl')
        next_page = None
        prev_page = None
        if page_number == 0:
            filename = 'index.html'
            if not is_last_page:
                next_page = 'page1.html'
        else:
            if not is_last_page:
                next_page = f'page{page_number + 1}.html'
            prev_page = 'index.html' if page_number == 1 else f"page{page_number - 1}.html"
            filename = f'page{page_number}.html'
        output = Path(workdir) / Path(filename)
        with output.open('w') as outfile:
            template.stream(entries=entries, title=self.title, prev_page=prev_page, next_page=next_page).dump(outfile)
        return filename

    def make_index(self, workdir):
        """
        """
        entries = []
        page_number = 0
        for file_number, (file, file_type) in enumerate(self.files, start=1):
            index_page = '../index.html' if page_number == 0 else f"../page{page_number}.html"
            entry = {'type': file_type, 'link_text': file.name, 'img_number': file_number,
                     'total_images': len(self.files), 'index_page': index_page,
                     'title': file.name}
            if file_type == 'image':
                entry['link'] = f'images/{file.stem}.html'
                self.make_image(file, entry, workdir)
            else:
                entry['link'] = f'images/{file.name}'
                shutil.copy(file, self.image_dir)
            entries.append(entry)
            if len(entries) == self.per_page:
                self._write_page(workdir, entries, page_number, file_number == len(self.files) + 1)
                entries = []
                page_number += 1
        if entries:
            self._write_page(workdir, entries, page_number, True)

    def copy_resources(self, output_dir):
        """
        """
        resource_source = self.template_dir / 'resources'
        resource_target = output_dir / 'resources'
        resource_target.mkdir(exist_ok=True)
        for resource in resource_source.glob('*'):
            shutil.copy(resource, resource_target)

    def _create_remote_directory(self, sftp, directory):
        """
        """
        try:
            sftp.stat(directory)
        except Exception:
            sftp.mkdir(directory)
            _logger.info(f"Created {directory}")

    def upload(self, workdir):
        """Upload directory to server
        """
        target = self.config['target']
        password = base64.b64decode(target['password']).decode()
        upload_base = target['directory'] + '/' + self.input_dir.name.lower().replace(' ', '')
        _logger.info(f"Uploading to {upload_base}")
        with paramiko.Transport((target['server'], target.get('port', 22))) as transport:
            transport.connect(username=target['username'], password=password)
            with paramiko.SFTPClient.from_transport(transport) as sftp:
                self._create_remote_directory(sftp, upload_base)
                for file in self.output_dir.glob('*.html'):
                    _logger.info(f"Uploading {file.name}")
                    sftp.put(file, upload_base + f'/{file.name}')
                for subdir in ['images', 'resources', 'thumbs']:
                    self._create_remote_directory(sftp, upload_base + f'/{subdir}')
                    src_dir = self.output_dir / Path(subdir)
                    for file in src_dir.glob('*'):
                        _logger.info(f"Uploading {file.name}")
                        sftp.put(file, upload_base + f'/{subdir}/{file.name}')

    def execute(self):
        """
        """
        _logger.info(f"Workdir is {self.output_dir}")
        _logger.info(f"Input dir is {self.input_dir}")
        _logger.info(f"Title is {self.title}")
        self.scan_input_dir()
        self.make_index(self.output_dir)
        self.copy_resources(self.output_dir)
        self.upload(self.output_dir)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = ArgumentParser()
    parser.add_argument('--config_file')
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('--title')
    args = parser.parse_args()
    AlbumMaker(args.config_file, args.input_dir, args.output_dir, args.title).execute()
