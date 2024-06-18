import logging

import xml.etree.ElementTree as ET
from typing import Union
from client import Client
from models import SAML, StackConfiguration

SAML_URL = "/services/authentication/providers/SAML"


def get_saml_url() -> str:
    """
    Get the URL for a given stack

    :param stack_name: The name of the stack

    :return: The URL for the stack
    """
    return SAML_URL


def get_saml(client: Client) -> Union[SAML, None]:
    """
    Get the SAML configuration for a given stack

    :param client: The client to use for the request

    :return: The SAML configuration for the stack or None if not found
    """
    _, current_config = client.get(get_saml_url(), {}, {})
    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "s": "http://dev.splunk.com/ns/rest",
    }

    if not current_config or not isinstance(current_config, str):
        logging.info("No SAML configuration found")
        return None

    root = ET.fromstring(current_config)
    keys = root.findall(".//s:key", namespaces)
    entry_title = root.find(".//atom:entry/atom:title", namespaces)
    if not entry_title.text:
        logging.info("No SAML configuration found due to missing title")
        return None
    
    key_values = {key.attrib["name"]: key.text for key in keys}

    return SAML(
        name=entry_title.text if entry_title is not None else None,
        entity_id=key_values["entityId"],
        fqdn=key_values["fqdn"],
        port=int(key_values["redirectPort"]),
        sso_url=key_values["idpSSOUrl"],
        slo_url=key_values["idpSLOUrl"],
        sso_binding=key_values["ssoBinding"],
        slo_binding=key_values["sloBinding"],
        alias_email=key_values["attributeAliasMail"],
        alias_realname=key_values["attributeAliasRealName"],
        alias_roles=key_values["attributeAliasRole"],
    )


def set_saml(stack_config: StackConfiguration, client: Client) -> None:
    """
    Set the SAML configuration for a given stack

    :param stack_config: The stack configuration to use
    :param client: The client to use for the request

    :return: None
    """
    saml = stack_config.saml
    if not saml:
        logging.info("No SAML configuration found")
        return

    current_config = get_saml(client=client)
    if not current_config:
        _, _ = client.post(get_saml_url(), {}, saml.to_create_dict(), as_json=False)
        logging.debug("SAML configuration created")
    elif current_config != saml:
        _, _ = client.post(
            get_saml_url() + "/" + current_config.name,
            {},
            saml.to_update_dict(),
            as_json=False,
        )
        logging.debug("SAML configuration updated")
    else:
        logging.info("SAML configuration unchanged")
