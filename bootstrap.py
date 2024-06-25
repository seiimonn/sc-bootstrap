import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pydantic import ValidationError
from models import StackConfiguration, Config
from utilities import load_yaml_to_model
from client import Client

from features.allowlist import set_allowlist
from features.hec import set_hec
from features.index import set_indexes
from features.saml import set_saml
from features.role import set_roles
from features.samlrole import set_saml_mapping
from features.splunkbase_apps import set_splunkbase_apps

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description='Bootstrap a new Splunk Cloud instance')
    parser.add_argument('--env-file', help='Path to the environment file', required=True)
    parser.add_argument('--config-file', help='Path to the config file', required=False, default='config.yaml')
    args = parser.parse_args()

    try:
        config: Config = load_yaml_to_model(args.config_file, Config)
        stack_config: StackConfiguration = load_yaml_to_model(args.env_file, StackConfiguration)
        acs_client = Client(stack_name=stack_config.stack_name, proxy=config.proxy, is_stage=stack_config.is_stage)
        api_client = Client(stack_name=stack_config.stack_name, proxy=config.proxy, is_stage=stack_config.is_stage, is_acs=False, api_url=stack_config.api_url)
        logging.info("Read config and stack configuration")
    except FileNotFoundError as e:
        logging.error("File not found: %s", e)
        sys.exit(1)
    except ValidationError as e:
        for error in e.errors():
            logging.error(error["msg"].replace("Value error, ", ""))
        sys.exit(1)

    logging.info('Bootstrapping environment: %s', stack_config.stack_name)

    logging.info("Setting allowlist")
    set_allowlist(client=acs_client, stack_config=stack_config)

    logging.info("Setting indexes")
    set_indexes(stack_config=stack_config, client=acs_client)

    logging.info("Setting HEC")
    set_hec(stack_config=stack_config, client=acs_client)

    logging.info("Setting SAML")
    set_saml(stack_config=stack_config, client=api_client)

    logging.info("Setting roles")
    set_roles(stack_config=stack_config, client=api_client)

    logging.info("Setting SAML role mappings")
    set_saml_mapping(stack_config=stack_config, client=api_client)

    logging.info("Setting Splunkbase apps")
    set_splunkbase_apps(stack_config=stack_config, client=acs_client)

    logging.info("Bootstrap complete")

if __name__ == '__main__':
    main()