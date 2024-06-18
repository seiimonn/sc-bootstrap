import logging

from client import Client
from models import AllowList, StackConfiguration


IP_ALLOW_URL = "{stack_name}/adminconfig/v2/access/{feature}/ipallowlists"


FEATURE_ATTRIBUTE_MAP = {
    "search-ui": "search_ui",
    "search-api": "search_api",
    "s2s": "s2s",
    "hec": "hec",
}


def get_feature_url(stack_name: str, feature: str) -> str:
    """
    Get the URL for a given feature and stack

    :param stack_name: The name of the stack
    :param feature: The feature to get the URL for

    :return: The URL for the feature and stack
    """
    return IP_ALLOW_URL.format(stack_name=stack_name, feature=feature)


def get_allowlist(stack_name: str, client: Client) -> AllowList:
    """
    Get the IP allow configuration for a given stack and feature

    :param stack_name: The name of the stack
    :param feature: The feature to get the IP allow configuration for
    :param client: The client to use for the request

    :return: The IP allow configuration for the stack and feature
    """
    config = {}

    for feature, _ in FEATURE_ATTRIBUTE_MAP.items():
        logging.debug("Getting IP allow configuration for %s", feature)
        _, response = client.get(
            get_feature_url(stack_name=stack_name, feature=feature), {}, {}
        )
        logging.debug("IP allow configuration for %s: %s", feature, response)
        config[feature] = response.get("subnets", [])

    logging.info("Retrieved IP allow configuration for %s: %s", stack_name, config)
    return AllowList.model_validate(config)


def set_allowlist(stack_config: StackConfiguration, client: Client) -> None:
    """
    Set the IP allow configuration for a given stack

    :param stack: The name of the stack
    :param ip_allow: The IP allow configuration to set
    :param client: The client to use for the request

    :return: None
    """
    new_ip_allow = stack_config.allowlist
    current_ip_allow = get_allowlist(client=client, stack_name=stack_config.stack_name)
    for feature, attribute in FEATURE_ATTRIBUTE_MAP.items():
        to_delete = []
        to_add = []

        for subnet in getattr(new_ip_allow, attribute):
            if subnet not in getattr(current_ip_allow, attribute):
                to_add.append(subnet)

        for subnet in getattr(current_ip_allow, attribute):
            if subnet not in getattr(new_ip_allow, attribute):
                to_delete.append(subnet)

        if to_add:
            logging.info("Adding subnets to %s: %s", feature, to_add)
            client.post(
                url=get_feature_url(stack_name=stack_config.stack_name, feature=feature),
                headers={},
                data={"subnets": [str(subnet) for subnet in to_add]},
            )
            logging.info("Added subnets to %s: %s", feature, to_add)

        if to_delete:
            logging.info("Removing subnets from %s: %s", feature, to_delete)
            client.delete(
                url=get_feature_url(stack_name=stack_config.stack_name, feature=feature),
                headers={},
                data={"subnets": [str(subnet) for subnet in to_delete]},
            )
            logging.info("Removed subnets from %s: %s", feature, to_delete)

    logging.info("IP allow configuration set")
