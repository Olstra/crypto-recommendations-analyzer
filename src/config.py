import os
from dotenv import load_dotenv

from common.data_paths import PROJECT_ROOT


def get_config_info():
    """
    Gets the Config File path
    :return: The Path to the current config file
    """
    while True:
        if PROJECT_ROOT in os.listdir():
            os.chdir(PROJECT_ROOT)
            break
        os.chdir('..')
    load_dotenv()
    return {
        "api-key-claude": os.getenv("API_KEY_CLAUDE"),
        "api-key-gemini": os.getenv("API_KEY_GEMINI"),
        "api-key-gpt": os.getenv("API_KEY_GPT"),
        "api-key-grok": os.getenv("API_KEY_GROK")
    }


class Config:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True

        # initialize attributes
        data = get_config_info()
        self.api_key_claude = str(data["api-key-claude"])
        self.api_key_gemini = str(data["api-key-gemini"])
        self.api_key_gpt = str(data["api-key-gpt"])
        self.api_key_grok = str(data["api-key-grok"])

    def reload(self):
        """
        Reloads the config from the Environment
        :return: A instance of the Config
        """
        self.__init__()
        return self


# create unique instance of config
config_instance = Config()