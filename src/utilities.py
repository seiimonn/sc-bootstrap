import yaml
import os
import sys
import logging

from typing import Any

def load_yaml_to_model(path: str, model: Any) -> Any:
    if not os.path.exists(path):
        logging.error('File not found: %s', path)
        sys.exit(1)

    with open(path, 'r') as file:
        dict = yaml.safe_load(file)
        return model.model_validate(dict)
