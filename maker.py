from pathlib import Path
from argparse import ArgumentParser
import yaml
import logging
from jinja2 import FileSystemLoader, Environment
import tempfile
import shutil
from PIL import Image

_logger = logging.getLogger()


class AlbumnMaker:

    def __init__(self, config_file, input_dir, output_dir, title):
        """
        :param config_file: Yaml file with settings
        """
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
        self.template_dir = Path(__file__).parents[0] / Path('styles') / Path(self.style)
        self.environ = Environment(loader=FileSystemLoader(self.template_dir))
        self.title = title
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

    def make_index(self, workdir):
        """
        """
        template = self.environ.get_template('index.tmpl')
        entries = []
        for file_number, (file, file_type) in enumerate(self.files, start=1):
            entry = {'type': file_type, 'link_text': file.name, 'img_number': file_number,
                     'total_images': len(self.files)}
            if file_type == 'image':
                entry['link'] = f'images/{file.stem}.html'
                self.make_image(file, entry, workdir)
            else:
                entry['link'] = f'images/{file.name}'
                shutil.copy(file, self.image_dir)
            entries.append(entry)
        output = Path(workdir) / Path('index.html')
        with output.open('w') as outfile:
            template.stream(entries=entries, title=self.title).dump(outfile)

    def copy_resources(self, output_dir):
        """
        """
        resource_source = self.template_dir / 'resources'
        resource_target = output_dir / 'resources'
        resource_target.mkdir(exist_ok=True)
        for resource in resource_source.glob('*'):
            shutil.copy(resource, resource_target)

    def execute(self):
        """
        """
        _logger.info(f"Workdir is {self.output_dir}")
        self.scan_input_dir()
        self.make_index(self.output_dir)
        self.copy_resources(self.output_dir)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = ArgumentParser()
    parser.add_argument('config_file')
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('title')
    args = parser.parse_args()
    AlbumnMaker(args.config_file, args.input_dir, args.output_dir, args.title).execute()


