from pathlib import Path
from argparse import ArgumentParser
import logging
from jinja2 import FileSystemLoader, Environment
import shutil
from PIL import Image, ImageOps
import paramiko

from config import AlbumMakerConfig

_logger = logging.getLogger('maker')


class AlbumMaker:
    """Create an album of school work and upload via SFTP
    """

    def configure(self, config_file, input_dir, title, who):
        """
        :param config_file: Yaml file with settings, if None will look for config.yml in this directory
        :param input_dir: Directory with input files
        :param title: If none will default to directory name of input
        :param who:
        """
        self.who = who
        self._config = AlbumMakerConfig(config_file)

        self.input_dir = Path(input_dir)
        self.album_dirname = self.input_dir.name.lower().replace(' ', '')
        self.output_dir = Path(self._config.local_dir) / Path(self.who) / Path(self.album_dirname)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.image_dir = self.output_dir / Path('images')
        self.image_dir.mkdir(exist_ok=True)
        self.thumb_dir = self.output_dir / Path('thumbs')
        self.thumb_dir.mkdir(exist_ok=True)

        if title is None:
            self.title = self.input_dir.name

        self.template_dir = Path(__file__).parents[0] / Path('styles') / Path(self._config.style)
        self.environ = Environment(loader=FileSystemLoader(self.template_dir))
        _logger.info(f"Workdir is {self.output_dir}")
        _logger.info(f"Input dir is {self.input_dir}")
        _logger.info(f"Title is {self.title}")
        return self

    def scan_input_dir(self):
        """Scan input dir for files
        """
        self.files = []
        for file in sorted(self.input_dir.glob('*')):
            file_suffix = file.suffix.lower()
            if file_suffix in self._config.image_suffix:
                _logger.info(f"Adding {file}")
                self.files.append((file, 'image'))
            elif file_suffix in self._config.movie_suffix:
                _logger.info(f"Adding {file}")
                self.files.append((file, 'movie'))
            elif file_suffix in self._config.doc_suffix:
                _logger.info(f"Adding {file}")
                self.files.append((file, 'doc'))

    def make_image(self, file, entry, workdir):
        """Make page for an image
        """
        template = self.environ.get_template('image.tmpl')
        output = Path(workdir) / Path('images') / Path(entry["html_file"])
        if entry['type'] == 'image':
            with Image.open(file) as im:
                im = ImageOps.exif_transpose(im)
                im.thumbnail(self._config.thumbnail_size)
                thumbfile = self.thumb_dir / Path(file.name)
                im.save(thumbfile)
                entry['thumb_width'] = im.width
                entry['thumb_height'] = im.height
            with Image.open(file) as im:
                im = ImageOps.exif_transpose(im)
                im.thumbnail(self._config.image_size)
                resized_file = self.image_dir / Path(file.name)
                im.save(resized_file)
                entry['image_width'] = im.width
                entry['image_height'] = im.height
        else:
            entry['image_height'] = self._config.image_size[1]
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
            template.stream(entries=entries, title=self.title, prev_page=prev_page, next_page=next_page,
                            thumb_x=self._config.thumbnail_size[0],
                            thumb_y=self._config.thumbnail_size[1],
                            who=self.who.capitalize()).dump(outfile)
        return filename

    def make_index(self, workdir):
        """
        """
        entries = []
        page_number = 0
        for file_number, (file, file_type) in enumerate(self.files, start=1):
            index_page = '../index.html' if page_number == 0 else f"../page{page_number}.html"
            entry = {'type': file_type, 'link_text': file.name, 'img_number': file_number,
                     'next_image': f"image_{file_number+1}.html" if file_number < len(self.files) else None,
                     'prev_image': f"image_{file_number-1}.html" if file_number > 1 else None,
                     'total_images': len(self.files), 'index_page': index_page,
                     'title': file.name}
            entry['html_file'] = f'image_{file_number}.html'
            entry['link'] = f'images/{entry["html_file"]}'
            self.make_image(file, entry, workdir)
            if file_type == 'doc' or file_type == 'movie':
                shutil.copy(file, self.image_dir)
            entries.append(entry)
            if len(entries) == self._config.per_page:
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

    def upload(self):
        """Upload directory to server
        """
        upload_base = self._config.target_directory + '/' + self.who + '/' + \
            self.input_dir.name.lower().replace(' ', '')
        _logger.info(f"Uploading to {upload_base}")
        with paramiko.Transport((self._config.target_server, self._config.target_port)) as transport:
            transport.connect(username=self._config.target_username, password=self._config.target_password)
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
        url = self._config.target_url + upload_base + '/index.html'
        _logger.info(url)
        return url

    def generate(self):
        """
        """
        self.scan_input_dir()
        self.make_index(self.output_dir)
        self.copy_resources(self.output_dir)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = ArgumentParser()
    parser.add_argument('who')
    parser.add_argument('input_dir')
    parser.add_argument('command', choices=['generate', 'upload'])
    parser.add_argument('--title')
    parser.add_argument('--config_file')
    parser.add_argument('--noupload', action='store_true')
    args = parser.parse_args()
    maker = AlbumMaker().configure(args.config_file, args.input_dir, args.title, args.who)
    getattr(maker, args.command)()
