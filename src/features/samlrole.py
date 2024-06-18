import logging

from typing import List
from client import Client
from models import SAMLRoleMapping, StackConfiguration

SAML_MAPPING_URL = "/services/admin/SAML-groups?output_mode=json&count=0"
SAML_ROLE_MAPPING_URL = "/services/admin/SAML-groups/{group}"

def get_saml_mapping_url() -> str:
    """
    Get the URL for a given stack

    :param stack_name: The name of the stack

    :return: The URL for the stack
    """
    return SAML_MAPPING_URL

def get_saml_group_mapping_url(group: str) -> str:
    """
    Get the URL for a given stack

    :param stack_name: The name of the stack

    :return: The URL for the stack
    """
    return SAML_ROLE_MAPPING_URL.format(group=group)


def get_saml_mapping(client: Client) -> List[SAMLRoleMapping]:
    """
    Get the SAML role mapping configuration

    :param client: The client to use for the request

    :return: The SAML role mapping configuration
    """
    _, response = client.get(get_saml_mapping_url(), {}, {})
    if not response or not isinstance(response, dict):
        raise ValueError("Invalid response from server - expected dictionary")

    role_content = response.get("entry", [])
    return [
        SAMLRoleMapping(
            group=role["name"],
            roles=role["content"]["roles"],
        )
        for role in role_content
    ]


def set_saml_mapping(stack_config: StackConfiguration, client: Client) -> None:
    """
    Fetches current SAML role mapping configuration and updates it based on the stack configuration
    If new mappings are found, they are created and added
    If mappings are missing, they are deleted

    :param stack_config: The stack configuration to use
    :param client: The client to use for the request

    :return: None
    """
    new_mappings = stack_config.saml_role_mappings
    new_mapping_names = [mapping.group for mapping in new_mappings]

    current_mappings = get_saml_mapping(client=client)
    current_mapping_names = [mapping.group for mapping in current_mappings]

    to_delete = []
    to_add = []
    to_update = []

    for mapping in new_mappings:
        if mapping.group not in current_mapping_names:
            to_add.append(mapping)
        else:
            current_mapping = next(
                (m for m in current_mappings if m.group == mapping.group), None
            )
            if current_mapping is not None and current_mapping != mapping:
                to_update.append(mapping)

    for mapping in current_mappings:
        if mapping.group not in new_mapping_names:
            to_delete.append(mapping)

    for mapping in to_delete:
        if stack_config.should_delete:
            logging.info("Deleting SAML role mapping: %s", mapping.group)
            client.delete(
                get_saml_group_mapping_url(mapping.group),
                {},
                {},
                as_json=False,
            )
            logging.info("SAML role mapping deleted: %s", mapping.group)
        else:
            logging.warning("Would have deleted SAML role mapping: %s", mapping.group)

    for mapping in to_add:
        logging.info("Creating SAML role mapping: %s", mapping.group)
        client.post(
            get_saml_mapping_url(),
            {},
            mapping.to_create_dict(),
            as_json=False,
        )
        logging.info("SAML role mapping created: %s", mapping.group)

    for mapping in to_update:
        logging.info("Updating SAML role mapping: %s", mapping.group)
        client.post(
            get_saml_group_mapping_url(mapping.group),
            {},
            mapping.to_update_dict(),
            as_json=False,
        )
        logging.info("SAML role mapping updated: %s", mapping.group)

    logging.info("SAML role mapping updated")
