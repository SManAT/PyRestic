import yaml
import logging
import random
import os
from pathlib import Path
from libs.OSDetector import OSDetector


class Configuration:
    """Handles <config>.yml File"""

    low = "abcdefghijklmnopqrstuvwxyz"
    upp = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    num = "0123456789"
    sym = "!@#$%^&*"

    def __init__(self, configFile):
        """
        :param configFile: Full Path to config File
        """
        self.logger = logging.getLogger(__name__)
        self.rootDir = Path(__file__).parent
        self.configFile = configFile

    def getDefaultConfig(self, profileName=None):
        if profileName is None:
            profileName = "default"

        if OSDetector.is_windows():
            config_dict = {
                f"{profileName}": {
                    "snapshots": 4,
                    "password": f"{self.createRandomPassword()}",
                    "storage": os.path.abspath(os.path.join(self.rootDir, "..", "STORAGE")),
                    "include": ["**/*", "C:\\Test"],
                    "exclude": ["Thumbs.db", "*.iso", "**/node_modules/**", "AI/**", ".lock*", "GitHub"],
                }
            }
        if OSDetector.is_linux():
            config_dict = {
                f"{profileName}": {
                    "snapshots": 4,
                    "password": f"{self.createRandomPassword()}",
                    "storage": "/backup/restic/storage",
                    "include": ["**/*", "/root/", "/var/www"],
                    "exclude": [
                        "Thumbs.db",
                        "*.iso",
                        "**/node_modules/**",
                        ".lock*",
                        "/root/.ansible/**",
                        "/root/.cache/**",
                        "/root/.composer/**",
                        "/root/.config/**",
                        "/root/.cpan/**",
                        "/root/.npm/**",
                        "/root/.local/**",
                        "/root/snap/**",
                    ],
                }
            }
        return config_dict

    def getConfigFilePath(self):
        return self.configFile

    def createRandomPassword(self, length=32):
        """create a random Password"""
        all = self.low + self.upp + self.num + self.sym
        return "".join(random.sample(all, length))

    def createEmptyConfigFile(self):
        """will create an Empty Config File"""
        try:
            self.save_config(self.getDefaultConfig(), self.configFile)

        except Exception as e:
            self.logger.error(f"Error creating config: {str(e)}")
            raise

    def save_config(self, config_dict, filepath="config.yml"):
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as file:
                yaml.dump(config_dict, file, sort_keys=False, default_flow_style=False)

        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            raise

    def load_config(self):
        return self.load_yml()

    def load_yml(self):
        """load the yml File"""
        with open(self.configFile, "rt", encoding="utf-8") as f:
            yml = yaml.safe_load(f.read())
        return yml

    def appendConfigFile(self, new_dict):
        """append new dict to existing config file"""
        old_config = self.load_yml()

        dest = {}
        dest.update(old_config)
        dest.update(new_dict)

        return dest
