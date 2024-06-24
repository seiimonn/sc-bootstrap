import logging

from typing import List
from client import Client
from models import HecToken, StackConfiguration

HEC_URL = "{stack}/adminconfig/v2/inputs/http-event-collectors"
DEFAULT_HEC_NAME = "victoriahec"


def get_hec_url(stack: str) -> str:
    """
    Get the URL for a given stack

    :param stack: The name of the stack

    :return: The URL for the stack
    """
    return HEC_URL.format(stack=stack)


def get_hec(stack_name: str, client: Client) -> List[HecToken]:
    """
    Get the HEC configuration for a given stack

    :param stack_name: The name of the stack
    :param client: The client to use for the request

    :return: The HEC configuration for the stack
    """
    _, response = client.get(get_hec_url(stack=stack_name), {}, {})
    logging.debug("HEC configuration for %s: %s", stack_name, response)

    if not isinstance(response, dict) or "http-event-collectors" not in response:
        logging.info("Did not find any existing HEC configuration")
        return []

    collectors = response.get("http-event-collectors", [])

    return [
        HecToken(
            token=collector["token"],
            name=collector["spec"].get("name"),
            default_index=collector["spec"].get("defaultIndex"),
            default_source=collector["spec"].get("defaultSource"),
            default_sourcetype=collector["spec"].get("defaultSourcetype"),
            disabled=collector["spec"].get("disabled", False),
            allowed_indexes=collector["spec"].get("allowedIndexes", []) or [],
            use_ack=collector["spec"].get("useAck", False),
        )
        for collector in collectors
    ]


def set_hec(stack_config: StackConfiguration, client: Client) -> None:
    """
    Fetches current HEC configuration and updates it based on the stack configuration
    If new tokens are found, they are created and added
    If tokens are missing, they are deleted

    :param stack_config: The stack configuration to use
    :param client: The client to use for the request

    :return: None
    """
    new_hec = stack_config.hec
    new_hec_names = [hec.name for hec in new_hec]

    current_hec = get_hec(client=client, stack_name=stack_config.stack_name)
    current_hec_names = [hec.name for hec in current_hec]

    to_delete = []
    to_add = []
    to_update = []

    for token in new_hec:
        if token.name not in current_hec_names:
            to_add.append(token)
        elif token not in current_hec:
            to_update.append(token)

    for token in current_hec:
        if token.name not in new_hec_names and token.name != DEFAULT_HEC_NAME:
            to_delete.append(token)

    for token in to_delete:
        if stack_config.should_delete:
            logging.info("Deleting HEC token %s", token.name)
            client.delete(
                get_hec_url(stack=stack_config.stack_name) + f"/{token.name}",
                {},
                {},
            )
            logging.info("HEC token deleted: %s", token.name)
        else:
            logging.warning("Would have deleted HEC token %s", token.name)

    for token in to_add:
        logging.info("Creating HEC token %s", token.name)
        client.post(
            get_hec_url(stack=stack_config.stack_name), {}, token.to_create_dict(),
        )
        logging.info("HEC token created: %s", token.name)

    for token in to_update:
        logging.info("Updating HEC token %s", token.name)
        client.patch(
            get_hec_url(stack=stack_config.stack_name) + f"/{token.name}",
            {},
            token.to_update_dict(),
        )

    logging.info("HEC configuration updated")