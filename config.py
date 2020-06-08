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
            if not config_file.exists():
                self._create_empty_config(config_file)        

        with open(config_file) as infile:
            self._config = yaml.safe_load(infile)

        self._image_suffix = self._config.get('image_suffix', ['.jpg'])
        self._other_suffix = self._config.get('other_suffix', ['.pdf', '.mov', '.mp4'])
        self._per_page = self._config.get('per_page', 12)
        self._style = self._config.get('style', 'default')
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
        self._save_config(config_file)

    @property
    def local_dir(self):
        """
        """
        return self._local_dir

    @property
    def image_suffix(self):
        return self._image_suffix
    
    @property
    def other_suffix(self):
        return self._other_suffix
    
    @property
    def per_page(self):
        return self._per_page

    @property
    def style(self):
        return self._style

    @property
    def thumbnail_size(self):
        return self._thumbnail_size
    
    @property
    def image_size(self):
        return self._image_size
    
    @property
    def who(self):
        return self._who
        
    @property
    def target_password(self):
        return base64.b64decode(self._target_password).decode()

    @property
    def target_directory(self):
        return self._target_directory
        
    @property
    def target_server(self):
        return self._target_server
    
    @property
    def target_url(self):
        return self._target_url
    
    @property
    def target_username(self):
        return self._target_username
    
    @property
    def target_port(self):
        return self._target_port
    
    def _create_empty_config(self, config_file):
        """
        """
        with config_file.open('w') as outfile:
            data = {'target': {'directory': self._target_directory, 'password': self._target_password, 'username': self._target_username, 'url': self._target_url, 
                               'server': self._target_server}, 
                    'who': ['person1'], 'per_page': 12, 'image_size': [500, 500], 'thumbnail_size': [240, 240]}
            yaml.dump(data, outfile)

    def _save_config(self, config_file):
        """
        """
        with config_file.open('w') as outfile:
            yaml.dump({'target':  {'directory': self._target_directory, 'password': self._target_password, 'username': self._target_username, 'url': self._target_url, 
                                   'server': self._target_server, 'port': self._target_port}, 
                       'who': self.who, 'per_page': self.per_page, 'image_size': self.image_size,
                'thumbnail_size': self.thumbnail_size, 'style': self.style, 'local_dir': str(self.local_dir),
                'image_suffix': self.image_suffix, 'other_suffix': self.other_suffix}, outfile)
