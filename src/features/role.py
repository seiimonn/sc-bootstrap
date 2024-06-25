import logging

from typing import List
from client import Client
from models import Role, StackConfiguration

ROLE_URL = "/services/authorization/roles?output_mode=json"
ROLE_NAME_URL = "/services/authorization/roles/{role_name}?output_mode=json"

DEFAULT_ROLES = [
    "admin",
    "can_delete",
    "power",
    "user",
    "sc_admin",
    "apps",
    "list_users_roles",
    "tokens_auth",
]


def get_role_url() -> str:
    """
    Get the URL for a given stack

    :param stack_name: The name of the stack

    :return: The URL for the stack
    """
    return ROLE_URL


def get_role_name_url(role_name: str) -> str:
    """
    Get the URL for a given role

    :param role_name: The name of the role

    :return: The URL for the role
    """
    return ROLE_NAME_URL.format(role_name=role_name)


def get_roles(client: Client) -> List[Role]:
    """
    Get the role configuration for a given stack

    :param client: The client to use for the request

    :return: The role configuration for the stack
    """
    _, response = client.get(get_role_url(), {}, {})
    if not response or not isinstance(response, dict):
        raise ValueError("Invalid response from server - expected dictionary")

    role_content = response.get("entry", [])
    return [
        Role(
            name=role["name"],
            imported_roles=role["content"]["imported_roles"],
            capabilities=role["content"]["capabilities"],
            default_app=role["content"]["defaultApp"],
            search_indexes_allowed=role["content"]["srchIndexesAllowed"],
            search_indexes_default=role["content"]["srchIndexesDefault"],
            search_filter=role["content"]["srchFilter"],
            search_disk_quota=role["content"]["srchDiskQuota"],
            search_job_quota=role["content"]["srchJobsQuota"],
            search_time_window=role["content"]["srchTimeWin"],
        )
        for role in role_content
    ]


def set_roles(stack_config: StackConfiguration, client: Client) -> None:
    """
    Fetches current role configuration and updates it based on the stack configuration
    If new roles are found, they are created and added
    If roles are missing, they are deleted

    :param stack_config: The stack configuration to use
    :param client: The client to use for the request

    :return: None
    """
    new_roles = stack_config.roles
    new_role_names = [role.name for role in new_roles]

    current_roles = get_roles(client=client)
    current_role_names = [role.name for role in current_roles]

    to_delete = []
    to_add = []
    to_update = []

    for role in new_roles:
        if role.name not in current_role_names:
            to_add.append(role)
        else:
            current_role = next((r for r in current_roles if r.name == role.name), None)
            if role != current_role and role.name not in DEFAULT_ROLES:
                to_update.append(role)

    for role in current_roles:
        if role.name not in new_role_names and role.name not in DEFAULT_ROLES:
            to_delete.append(role)

    for role in to_delete:
        if stack_config.should_delete:
            logging.info("Deleting role %s", role.name)
            client.delete(
                get_role_name_url(role_name=role.name),
                {},
                {},
                as_json=False,
            )
            logging.info("Role deleted: %s", role.name)
        else:
            logging.warning("Would have deleted role %s", role.name)

    for role in to_add:
        logging.info("Creating role %s", role.name)
        client.post(get_role_url(), {}, role.to_create_dict(), as_json=False,)
        logging.info("Role created: %s", role.name)

    for role in to_update:
        logging.info("Updating role %s", role.name)
        client.post(
            get_role_name_url(role_name=role.name),
            {},
            role.to_update_dict(),
            as_json=False,
        )
        logging.info("Role updated: %s", role.name)

    logging.info("Role configuration updated")
