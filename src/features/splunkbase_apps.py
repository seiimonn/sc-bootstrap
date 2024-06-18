import logging

from typing import List
from client import Client
from models import SplunkbaseApp, StackConfiguration


SPLUNKBASE_APPS_URL = "{stack_name}/adminconfig/v2/apps/victoria?splunkbase=true"
SPLUNKBASE_APPS_APP_URL = "{stack_name}/adminconfig/v2/apps/victoria/{app_id}"

DEFAULT_APP_IDS = [
    "5137",
    "5483",
    "1876",
]


def get_splunkbase_apps_url(stack_name: str) -> str:
    """
    Get the URL for a given stack

    :param stack_name: The name of the stack

    :return: The URL for the stack
    """
    return SPLUNKBASE_APPS_URL.format(stack_name=stack_name)

def get_splunkbase_app_url(stack_name: str, app_id: str) -> str:
    """
    Get the URL for a given stack and app

    :param stack_name: The name of the stack
    :param app_id: The ID of the app

    :return: The URL for the stack and app
    """
    return SPLUNKBASE_APPS_APP_URL.format(stack_name=stack_name, app_id=app_id)

def get_splunkbase_apps(stack_name: str, client: Client) -> List[SplunkbaseApp]:
    """
    Get the Splunkbase apps for a given stack

    :param stack_name: The name of the stack
    :param client: The client to use for the request

    :return: The Splunkbase apps for the stack
    """
    _, response = client.get(get_splunkbase_apps_url(stack_name=stack_name), {}, {})

    return [
        SplunkbaseApp(
            splunkbase_id=app["splunkbaseID"],
            version=app["version"],
            app_id=app["appID"],
        )
        for app in response["apps"]
    ]

def set_splunkbase_apps(stack_config: StackConfiguration, client: Client) -> None:
    """
    Fetches current Splunkbase apps configuration and updates it based on the stack configuration
    If new apps are found, they are installed from Splunkbase
    If app versions are different, they are updated
    If apps are missing, they are deleted

    :param stack_config: The stack configuration to use
    :param client: The client to use for the request
    """
    new_apps = stack_config.splunkbase_apps
    new_app_ids = [app.splunkbase_id for app in new_apps]

    current_apps = get_splunkbase_apps(stack_config.stack_name, client)
    current_app_ids = [app.splunkbase_id for app in current_apps]

    to_add = []
    to_update = []
    to_delete = []

    for app in new_apps:
        if app.splunkbase_id not in current_app_ids:
            to_add.append(app)
        elif app not in current_apps:
            to_update.append(app)

    for app in current_apps:
        if app.splunkbase_id not in new_app_ids and app.splunkbase_id not in DEFAULT_APP_IDS:
            to_delete.append(app)

    if not (to_add or to_update or to_delete):
        logging.info("No changes to Splunkbase apps")
        return

    client.authenticate_splunkbase()

    for app in to_delete:
        if stack_config.should_delete:
            logging.info("Deleting app %s", app.splunkbase_id)
            client.delete(
                get_splunkbase_app_url(stack_name=stack_config.stack_name, app_id=app.app_id),
                {},
                {},
            )
            logging.info("Requested uninstall for app %s", app.splunkbase_id)
        else:
            logging.warning("Would have deleted app %s", app.splunkbase_id)

    for app in to_add:
        logging.info("Adding app %s", app.splunkbase_id)
        client.post(
            get_splunkbase_apps_url(stack_name=stack_config.stack_name),
            {"ACS-Licensing-Ack": app.license_url},
            app.to_create_dict(),
            as_json=False
        )
        logging.info("Requested install for app %s", app.splunkbase_id)

    for app in to_update:
        logging.info("Updating app %s", app.splunkbase_id)
        current_app = next(a for a in current_apps if a.splunkbase_id == app.splunkbase_id)
        client.patch(
            get_splunkbase_app_url(stack_name=stack_config.stack_name, app_id=current_app.app_id),
            {"ACS-Licensing-Ack": app.license_url},
            app.to_update_dict(),
            as_json=False
        )
        logging.info("Requested update for app %s", app.splunkbase_id)

