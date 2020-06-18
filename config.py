import yaml
import base64
from pathlib import Path


class AlbumMakerConfig:
    """
    """

    def __init__(self, config_file=None):
        """
        """
        if config_file is None:
            config_path = Path.home() / Path('.amaker')
            config_file = config_path / Path('config.yml')
            if not config_path.exists():
                config_path.mkdir()
            if config_file.exists():
                with open(config_file) as infile:
                    self._config = yaml.safe_load(infile)
            else:
                self._config = {}

        self._yaml_file = config_file
        self._image_suffix = self._config.get('image_suffix', ['.jpg'])
        self._movie_suffix = self._config.get('movie_suffix', ['.mov', '.mp4'])
        self._doc_suffix = self._config.get('doc_suffix', ['.pdf'])
        self._per_page = self._config.get('per_page', 12)
        self._style = self._config.get('style', 'boostrap')
        self._thumbnail_size = self._config.get('thumbnail_size', [240, 240])
        self._image_size = self._config.get('image_size', [500, 500])
        self._local_dir = self._config.get('local_dir', str(Path.home() / Path('albums')))
        self._target = self._config.get('target', {})
        self._target_password = self._target.get('password')
        self._target_directory = self._target.get('directory')
        self._target_server = self._target.get('server')
        self._target_port = self._target.get('port', 22)
        self._target_url = self._target.get('url')
        self._target_username = self._target.get('username')
        self._who = self._config.get('who', ['noname'])
        self.save()

    @property
    def local_dir(self):
        """
        """
        return self._local_dir

    @local_dir.setter
    def local_dir(self, value):
        if not Path(value).is_dir():
            raise ValueError(f"{value} is not a valid directory")
        self._local_dir = value

    @property
    def image_suffix(self):
        return self._image_suffix

    @property
    def movie_suffix(self):
        return self._movie_suffix

    @property
    def doc_suffix(self):
        return self._doc_suffix

    @property
    def per_page(self):
        return self._per_page

    @per_page.setter
    def per_page(self, value):
        self._per_page = value

    @property
    def style(self):
        return self._style

    @property
    def thumbnail_size(self):
        return self._thumbnail_size

    @thumbnail_size.setter
    def thumbnail_size(self, value):
        self._thumbnail_size = value

    @property
    def image_size(self):
        return self._image_size

    @image_size.setter
    def image_size(self, value):
        self._image_size = value

    @property
    def who(self):
        return self._who

    @property
    def target_password(self):
        if self._target_password:
            return base64.b64decode(self._target_password).decode()
        return ''

    @target_password.setter
    def target_password(self, value):
        self._target_password = base64.b64encode(value.encode()).decode()

    @property
    def target_directory(self):
        return self._target_directory

    @target_directory.setter
    def target_directory(self, value):
        self._target_directory = value

    @property
    def target_server(self):
        return self._target_server

    @target_server.setter
    def target_server(self, value):
        self._target_server = value

    @property
    def target_url(self):
        return self._target_url

    @target_url.setter
    def target_url(self, value):
        self._target_url = value

    @property
    def target_username(self):
        return self._target_username

    @target_username.setter
    def target_username(self, value):
        self._target_username = value

    @property
    def target_port(self):
        return self._target_port

    def _create_empty_config(self, config_file):
        """
        """
        with config_file.open('w') as outfile:
            data = {'target': {'directory': self.target_directory, 'password': self._target_password,
                               'username': self.target_username, 'url': self.target_url,
                               'server': self.target_server},
                    'who': ['person1'], 'per_page': 12, 'image_size': [500, 500], 'thumbnail_size': [240, 240]}
            yaml.dump(data, outfile)

    def save(self):
        """
        """
        with self._yaml_file.open('w') as outfile:
            yaml.dump({'target': {'directory': self._target_directory, 'password': self._target_password,
                                  'username': self._target_username, 'url': self._target_url,
                                  'server': self._target_server, 'port': self._target_port},
                       'who': self.who, 'per_page': self.per_page, 'image_size': self.image_size,
                       'thumbnail_size': self.thumbnail_size, 'style': self.style, 'local_dir': str(self.local_dir),
                       }, outfile)
