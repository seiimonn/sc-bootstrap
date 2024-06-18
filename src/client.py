import os
import requests
import logging

import xml.etree.ElementTree as ET
from typing import Any, Dict, Tuple, Union, List
from models import Proxy

BASE_URLS = {
    "prod": "https://admin.splunk.com/",
    "stage": "https://staging.admin.splunk.com/",
}


class Client:
    def __init__(
        self,
        env: str,
        proxy: Proxy,
        is_stage: bool = False,
        is_acs: bool = True,
        api_url: str = "",
    ):
        self.env = env
        self.proxy = proxy
        self.is_stage = is_stage

        if is_acs:
            self.base_url = BASE_URLS["stage" if self.is_stage else "prod"]
        else:
            self.base_url = api_url

        self.token = os.environ.get(f"{env.upper()}_TOKEN")
        if not self.token:
            raise ValueError(f"Token not found for {env}")

        self.username = os.environ.get(f"{env.upper()}_USERNAME")
        if not self.username:
            raise ValueError(f"Username not found for {env}")

        self.password = os.environ.get(f"{env.upper()}_PASSWORD")
        if not self.password:
            raise ValueError(f"Password not found for {env}")

        self.headers = {"Authorization": f"Bearer {self.token}"}

        self.session = requests.Session()
        if self.proxy.used and self.proxy.url:
            if self.proxy.username and self.proxy.password:
                self.session.proxies = {
                    "http": f"http://{self.proxy.username}:{self.proxy.password}@{self.proxy.url}",
                    "https": f"https://{self.proxy.username}:{self.proxy.password}@{self.proxy.url}",
                }
            else:
                self.session.proxies = {
                    "http": str(self.proxy.url),
                    "https": str(self.proxy.url),
                }

    def __handle_response(
        self, response: requests.Response
    ) -> Tuple[int, Union[Dict[Any, Any], str, List]]:
        """
        Handle the response from the API - raise an error if the response is not successful
        If the response is JSON, return the JSON object, otherwise return the text
        """
        response.raise_for_status()

        if "content-type" in response.headers and response.headers[
            "content-type"
        ].startswith("application/json"):
            return response.status_code, response.json()

        return response.status_code, response.text

    def __convert_to_form_data(self, data: dict) -> List[Tuple[str, str]]:
        """
        Convert the data to form data format
        Converts lists to multiple key-value pairs
        """
        form_data = []
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    form_data.append((key, item))
            else:
                form_data.append((key, value))

        logging.error(form_data)
        return form_data
    
    def authenticate_splunkbase(self):
        """
        Authenticate with Splunkbase and set the necessary headers
        """
        response = self.session.post(
            "https://splunkbase.splunk.com/api/account:login", data={"username": self.username, "password": self.password}
        )
        response.raise_for_status()

        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(response.text)
        id_element = root.find('atom:id', namespace)

        if id_element is None or not id_element.text:
            raise ValueError("Invalid response from Splunkbase")
        
        self.session.headers.update({"X-Splunkbase-Authorization": id_element.text})

    def get(
        self, url: str, headers: Dict[str, str], params: dict
    ) -> Tuple[int, Union[Dict[Any, Any], str, List]]:
        response = self.session.get(
            self.base_url + url, headers={**self.headers, **headers}, params=params
        )
        return self.__handle_response(response)

    def post(
        self, url: str, headers: Dict[str, str], data: dict, as_json: bool = True
    ) -> Tuple[int, Union[Dict[Any, Any], str, List]]:
        if as_json:
            response = self.session.post(
                self.base_url + url, headers={**self.headers, **headers}, json=data
            )
        else:
            response = self.session.post(
                self.base_url + url, headers={**self.headers, **headers}, data=self.__convert_to_form_data(data)
            )
        return self.__handle_response(response)

    def put(
        self, url: str, headers: Dict[str, str], data: dict, as_json: bool = True
    ) -> Tuple[int, Union[Dict[Any, Any], str, List]]:
        if as_json:
            response = self.session.put(
                self.base_url + url, headers={**self.headers, **headers}, json=data
            )
        else:
            response = self.session.put(
                self.base_url + url, headers={**self.headers, **headers}, data=self.__convert_to_form_data(data)
            )
        return self.__handle_response(response)

    def patch(
        self, url: str, headers: Dict[str, str], data: dict, as_json: bool = True
    ) -> Tuple[int, Union[Dict[Any, Any], str, List]]:
        if as_json:
            response = self.session.patch(
                self.base_url + url, headers={**self.headers, **headers}, json=data
            )
        else:
            response = self.session.patch(
                self.base_url + url, headers={**self.headers, **headers}, data=self.__convert_to_form_data(data)
            )
        return self.__handle_response(response)

    def delete(
        self, url: str, headers: Dict[str, str], data: dict, as_json: bool = True
    ) -> Tuple[int, Union[Dict[Any, Any], str, List]]:
        if as_json:
            response = self.session.delete(
                self.base_url + url, headers={**self.headers, **headers}, json=data
            )
        else:
            response = self.session.delete(
                self.base_url + url, headers={**self.headers, **headers}, data=self.__convert_to_form_data(data)
            )
        return self.__handle_response(response)
