import os
import uuid

from pydantic import BaseModel, Field, model_validator
from pydantic.networks import IPvAnyNetwork

from enum import Enum
from typing import List, Union


class CustomBaseModel(BaseModel):
    class Config:
        extra = "forbid"
        allow_population_by_alias = True
        validate_assignment = True


class AllowList(CustomBaseModel):
    search_ui: List[IPvAnyNetwork] = Field(alias="search-ui", default=[])
    search_api: List[IPvAnyNetwork] = Field(alias="search-api", default=[])
    s2s: List[IPvAnyNetwork] = Field(default=[])
    hec: List[IPvAnyNetwork] = Field(default=[])

    class Config:
        extra = "forbid"
        allow_population_by_alias = True


class IndexType(str, Enum):
    EVENT = "event"
    METRIC = "metric"


class Index(CustomBaseModel):
    name: str
    datatype: IndexType = IndexType.EVENT
    maxmb: int = 1024 * 500
    days_searchable: int = 30

    def to_create_dict(self):
        return {
            "datatype": self.datatype,
            "maxDataSizeMB": self.maxmb,
            "name": self.name,
            "searchableDays": self.days_searchable,
        }

    def to_update_dict(self):
        return {
            "datatype": self.datatype,
            "maxDataSizeMB": self.maxmb,
            "searchableDays": self.days_searchable,
        }

    def __eq__(self, other):
        return all(
            [
                self.name == other.name,
                self.datatype == other.datatype,
                self.maxmb == other.maxmb,
                self.days_searchable == other.days_searchable,
            ]
        )


class HecToken(CustomBaseModel):
    name: str
    token: str
    default_index: str = "main"
    default_source: str = ""
    default_sourcetype: str = ""
    disabled: bool = False
    allowed_indexes: List[str] = []
    use_ack: bool = False

    def to_create_dict(self):
        return {
            "allowedIndexes": self.allowed_indexes,
            "defaultIndex": self.default_index,
            "defaultSource": self.default_source,
            "defaultSourcetype": self.default_sourcetype,
            "disabled": self.disabled,
            "name": self.name,
            "token": self.token,
        }

    def to_update_dict(self):
        return {
            "allowedIndexes": self.allowed_indexes,
            "defaultIndex": self.default_index,
            "defaultSource": self.default_source,
            "defaultSourcetype": self.default_sourcetype,
            "disabled": self.disabled,
            "useAck": self.use_ack,
        }

    def __eq__(self, other):
        return all(
            [
                self.name == other.name,
                self.token == other.token,
                self.default_index == other.default_index,
                self.default_source == other.default_source,
                self.default_sourcetype == other.default_sourcetype,
                self.disabled == other.disabled,
                set(self.allowed_indexes) == set(other.allowed_indexes),
                self.use_ack == other.use_ack,
            ]
        )


class SSOBinding(str, Enum):
    POST = "HTTP-POST"
    REDIRECT = "HTTP-RREDIRECT"


class SAMLScriptArg(CustomBaseModel):
    name: str
    env_var: str

    @property
    def value(self):
        if self.env_var in os.environ:
            return os.environ[self.env_var]

        raise ValueError(f"Environment variable {self.env_var} not found")

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }

    def to_string(self):
        return f"{self.name}:{self.value}"


class SAML(CustomBaseModel):
    name: str
    entity_id: str
    fqdn: str
    port: int = 8000
    cert: Union[None, str] = None
    sso_url: str
    slo_url: str
    sso_binding: SSOBinding = SSOBinding.POST
    slo_binding: SSOBinding = SSOBinding.POST
    alias_realname: str = "http://schemas.microsoft.com/identity/claims/displayname"
    alias_email: str = (
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    )
    alias_roles: str = "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"
    use_auth_extentsion_token_only: bool = True
    script_path: str = ""
    script_functions: List[str] = Field(default=["login", "getUserInfo"])
    script_args: List[SAMLScriptArg] = Field(default=[])

    def to_create_dict(self):
        return {
            "name": self.name,
            "entityId": self.entity_id,
            "fqdn": self.fqdn,
            "redirectPort": self.port,
            "idpSLOUrl": self.slo_url,
            "idpSSOUrl": self.sso_url,
            "ssoBinding": self.sso_binding,
            "sloBinding": self.slo_binding,
            "attributeAliasMail": self.alias_email,
            "attributeAliasRealName": self.alias_realname,
            "attributeAliasRole": self.alias_roles,
            "idpCertificatePayload": self.cert,
            "scriptPath": self.script_path,
            "scriptFunctions": self.script_functions,
            "scriptSecureArguments": [arg.to_string() for arg in self.script_args],
            "useAuthExtForTokenAuthOnly": self.use_auth_extentsion_token_only,
        }

    def to_update_dict(self):
        return {
            "entityId": self.entity_id,
            "fqdn": self.fqdn,
            "redirectPort": self.port,
            "idpSLOUrl": self.slo_url,
            "idpSSOUrl": self.sso_url,
            "ssoBinding": self.sso_binding,
            "sloBinding": self.slo_binding,
            "attributeAliasMail": self.alias_email,
            "attributeAliasRealName": self.alias_realname,
            "attributeAliasRole": self.alias_roles,
            "idpCertificatePayload": self.cert,
            "scriptPath": self.script_path,
            "scriptFunctions": self.script_functions,
            "scriptSecureArguments": [arg.to_string() for arg in self.script_args],
            "useAuthExtForTokenAuthOnly": self.use_auth_extentsion_token_only,
        }

    def __eq__(self, _) -> bool:
        # As we can not compare the script secure arguments we always return False
        return False


class Role(CustomBaseModel):
    name: str
    capabilities: List[str] = []
    default_app: str = "search"
    imported_roles: List[str] = []
    search_disk_quota: int = 100
    search_filter: str = ""
    search_indexes_allowed: List[str] = []
    search_indexes_default: List[str] = []
    search_job_quota: int = 100
    search_time_window: int = 0

    def to_create_dict(self):
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "defaultApp": self.default_app,
            "imported_roles": self.imported_roles,
            "srchDiskQuota": self.search_disk_quota,
            "srchFilter": self.search_filter,
            "srchIndexesAllowed": self.search_indexes_allowed,
            "srchIndexesDefault": self.search_indexes_default,
            "srchJobsQuota": self.search_job_quota,
            "srchTimeWin": self.search_time_window,
        }

    def to_update_dict(self):
        return {
            "capabilities": self.capabilities,
            "defaultApp": self.default_app,
            "imported_roles": self.imported_roles,
            "srchDiskQuota": self.search_disk_quota,
            "srchFilter": self.search_filter,
            "srchIndexesAllowed": self.search_indexes_allowed,
            "srchIndexesDefault": self.search_indexes_default,
            "srchJobsQuota": self.search_job_quota,
            "srchTimeWin": self.search_time_window,
        }

    def __eq__(self, other):
        return all(
            [
                self.name == other.name,
                set(self.capabilities) == set(other.capabilities),
                self.default_app == other.default_app,
                set(self.imported_roles) == set(other.imported_roles),
                self.search_disk_quota == other.search_disk_quota,
                self.search_filter == other.search_filter,
                set(self.search_indexes_allowed) == set(other.search_indexes_allowed),
                set(self.search_indexes_default) == set(other.search_indexes_default),
                self.search_job_quota == other.search_job_quota,
                self.search_time_window == other.search_time_window,
            ]
        )


class SAMLRoleMapping(CustomBaseModel):
    roles: List[str]
    group: str

    def to_create_dict(self):
        return {
            "roles": self.roles,
            "name": self.group,
        }

    def to_update_dict(self):
        return {
            "roles": self.roles,
        }

    def __eq__(self, other):
        return all(
            [
                set(self.roles) == set(other.roles),
                self.group == other.group,
            ]
        )


class SplunkbaseApp(CustomBaseModel):
    app_id: str = ""
    splunkbase_id: str
    version: str
    license_url: str = "https://www.splunk.com/en_us/legal/splunk-general-terms.html"

    def to_create_dict(self):
        return {
            "splunkbaseID": self.splunkbase_id,
            "version": self.version,
        }

    def to_update_dict(self):
        return {
            "version": self.version,
        }

    def __eq__(self, other):
        return all(
            [
                self.splunkbase_id == other.splunkbase_id,
                self.version == other.version,
            ]
        )


class StackConfiguration(CustomBaseModel):
    should_delete: bool = False
    stack_name: str
    api_url: str
    is_stage: bool = False
    allowlist: AllowList = Field(default=AllowList())
    hec: List[HecToken] = Field(default=[])
    indexes: List[Index] = Field(default=[])
    roles: List[Role] = Field(default=[])
    saml: Union[None, SAML] = Field(default=None)
    saml_role_mappings: List[SAMLRoleMapping] = Field(default=[])
    splunkbase_apps: List[SplunkbaseApp] = Field(default=[])

    @model_validator(mode="after")
    def verify_hec_tokens(self):
        hec_names = [hec.name for hec in self.hec]
        hec_tokens = [hec.token for hec in self.hec]

        if len(hec_names) != len(set(hec_names)):
            raise ValueError("Duplicate HEC names found")

        if len(hec_tokens) != len(set(hec_tokens)):
            raise ValueError("Duplicate HEC tokens found")

        for token in hec_tokens:
            try:
                uuid.UUID(token)
            except ValueError:
                raise ValueError(f"Invalid token {token}")

        return self

    @model_validator(mode="after")
    def verify_indexes(self):
        index_names = [index.name for index in self.indexes]

        if len(index_names) != len(set(index_names)):
            raise ValueError("Duplicate index names found")

        return self

    @model_validator(mode="after")
    def verify_roles(self):
        role_names = [role.name for role in self.roles]

        if len(role_names) != len(set(role_names)):
            raise ValueError("Duplicate role names found")

        return self

    @model_validator(mode="after")
    def verify_saml_role_mappings(self):
        group_names = [mapping.group for mapping in self.saml_role_mappings]

        if len(group_names) != len(set(group_names)):
            raise ValueError("Duplicate group names found")

        return self

    @model_validator(mode="after")
    def verify_splunkbase_apps(self):
        splunkbase_ids = [app.splunkbase_id for app in self.splunkbase_apps]

        if len(splunkbase_ids) != len(set(splunkbase_ids)):
            raise ValueError("Duplicate app IDs found")

        return self


class Proxy(CustomBaseModel):
    used: bool = False
    url: Union[None, str] = Field(default=None)
    username: Union[None, str] = Field(default=None)
    password: Union[None, str] = Field(default=None)


class Config(CustomBaseModel):
    proxy: Proxy = Field(default=Proxy())
