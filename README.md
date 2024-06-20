# Splunk Cloud Bootstrap (Victoria)

This repository contains a set of scripts and templates to help you get started with Splunk Cloud using the Victoria experience. The scripts are designed to be run on a local machine, and they will help you to configure your Splunk Cloud environment. In addition to bootstrapping the environment, the scripts can also be used to update the configuration of your environment. Make sure to set the `should_delete` flag to `True` in the configuration file to delete objects. Please be aware that certain objects cannot be updated or deleted, and you may need to manually remove them.

Currently, the following objects can be created:

- Indexes
- IP Allow List
- HEC Tokens
- Roles
- SAML Authentication
- SAML Role Mapping
- Splunkbase Apps

This repository is a work in progress, and we will be adding more features in the future. If you have any suggestions or feedback, please let us know by creating an issue.

Following features will not be supported in this repository:

- DDSS Locations (as the response has to be further processed to configure the bucket)
- Private Links (as the response has to be further processed to configure the link)

Planned features:

- Private Apps

## Prerequisites

- Token with a user that has the `sc_admin` role
- Username and password for a Splunkbase account

## Getting Started

1. Clone this repository
2. Install the required dependencies by running `pip install -r requirements.txt`
3. Copy the `example.yaml` file from the `configuration` directory and rename it to `<enironment_name>.yaml`
4. Update the configuration to reflect the expected state of your Splunk Cloud environment
5. Export the following environment variables:
    - `export <STACK_NAME>_TOKEN=<token>`
    - `export <STACK_NAME>_USERNAME=<username>`
    - `export <STACK_NAME>_PASSWORD=<password>`
    - The `<STACK_NAME>` should be the name of the environment you are configuring in uppercase and `_` instead of `-`.

## Usage

To create the objects in your Splunk Cloud environment, run the following command:

```bash
python bootstrap.py --env-file environments/<environment_name>.yaml --config-file configuraiton.yaml
```
