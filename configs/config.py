import tomli as tomllib
from typing import Optional, Type, Dict, TypeVar
from pydantic import BaseModel

from utils.logger import Logger
logger = Logger()

class ConfigModel(BaseModel):
    pass

class Configs:
    ConfigType = TypeVar('ConfigType', bound=ConfigModel)
    
    def __init__(self, file_path: str):
        self._settings: Dict[Type[Configs.ConfigType], Configs.ConfigType] = self._load_settings_from_toml(file_path)

    def _load_settings_from_toml(self, file_path: str) -> Dict[Type[ConfigType], ConfigType]:
        with open(file_path, "rb") as f:
            try:
                toml_content = tomllib.load(f)
                logger.info(f"TOML content loaded: {toml_content}")  # Debugging output
            except tomllib.TOMLDecodeError as e:
                logger.info(f"TOML file decoding error: {e}")
                toml_content = {}

        config_subclasses = ConfigModel.__subclasses__()
        logger.info(f"ConfigModel subclasses: {config_subclasses}")  # Debugging output
        configs = {
            config_class: config_class.parse_obj(toml_content[config_class.__name__])
            for config_class in config_subclasses
            if config_class.__name__ in toml_content
        }
        logger.info(f"Loaded configs: {configs}")  # Debugging output
        return configs

    def get(self, config_class: Type[ConfigType]) -> Optional[ConfigType]:
        return self._settings.get(config_class)
