import logging

from typing import List
from client import Client
from models import Index, StackConfiguration

INDEX_URL = "{stack_name}/adminconfig/v2/indexes"
DEFAULT_INDEX_NAMES = [
    "history",
    "ingest-actions-seed",
    "lastchanceindex",
    "main",
    "splunklogger",
    "summary",
]


def get_index_url(stack_name: str) -> str:
    """
    Get the URL for a given stack

    :param stack_name: The name of the stack

    :return: The URL for the stack
    """
    return INDEX_URL.format(stack_name=stack_name)


def get_indexes(stack_name: str, client: Client) -> List[Index]:
    """
    Get the index configuration for a given stack

    :param stack_name: The name of the stack
    :param client: The client to use for the request

    :return: The index configuration for the stack
    """
    _, response = client.get(get_index_url(stack_name=stack_name), {}, {})
    logging.debug("Index configuration for %s: %s", stack_name, response)

    return [
        Index(
            name=index.get("name"),
            datatype=index.get("datatype"),
            maxmb=index.get("maxDataSizeMB"),
            days_searchable=index.get("searchableDays"),
        )
        for index in response
    ]


def set_indexes(stack_config: StackConfiguration, client: Client) -> None:
    """
    Fetches current index configuration and updates it based on the stack configuration
    If new indexes are found, they are created and added
    If indexes are missing, they are deleted

    :param stack_config: The stack configuration to use
    :param client: The client to use for the request

    :return: None
    """
    new_indexes = stack_config.indexes
    new_indexe_names = [index.name for index in new_indexes]

    current_indexes = get_indexes(stack_name=stack_config.stack_name, client=client)
    current_index_names = [index.name for index in current_indexes]

    to_delete = []
    to_add = []
    to_update = []

    for index in new_indexes:
        if index.name not in current_index_names:
            to_add.append(index)
        elif index not in current_indexes:
            to_update.append(index)

    for index in current_indexes:
        if index.name not in new_indexe_names and index.name not in DEFAULT_INDEX_NAMES:
            to_delete.append(index)

    for index in to_delete:
        if stack_config.should_delete:
            logging.info("Deleting index %s", index.name)
            client.delete(
                get_index_url(stack_name=stack_config.stack_name) + f"/{index.name}",
                {},
                {},
            )
            logging.info("Index deleted: %s", index.name)
        else:
            logging.warning("Would have deleted index %s", index.name)

    for index in to_add:
        logging.info("Creating index %s", index.name)
        client.post(
            get_index_url(stack_name=stack_config.stack_name),
            {},
            index.to_create_dict(),
        )
        logging.info("Index created: %s", index.name)

    for index in to_update:
        logging.info("Updating index %s", index.name)
        client.patch(
            get_index_url(stack_name=stack_config.stack_name) + f"/{index.name}",
            {},
            index.to_update_dict(),
        )
        logging.info("Index updated: %s", index.name)

    logging.info("Index configuration updated")
