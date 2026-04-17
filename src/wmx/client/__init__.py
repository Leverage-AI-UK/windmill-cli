from __future__ import annotations

from wmx.client.apps import AppsAPI
from wmx.client.auth import AuthAPI
from wmx.client.docs import DocsAPI
from wmx.client.flows import FlowsAPI
from wmx.client.http import HttpClient
from wmx.client.jobs import JobsAPI
from wmx.client.resources import ResourcesAPI
from wmx.client.schedules import SchedulesAPI
from wmx.client.scripts import ScriptsAPI
from wmx.client.variables import VariablesAPI
from wmx.config import RuntimeConfig


class WindmillAPI:
    def __init__(self, config: RuntimeConfig) -> None:
        self.http = HttpClient(config)
        self.auth = AuthAPI(self.http)
        self.scripts = ScriptsAPI(self.http)
        self.flows = FlowsAPI(self.http)
        self.resources = ResourcesAPI(self.http)
        self.variables = VariablesAPI(self.http)
        self.jobs = JobsAPI(self.http)
        self.schedules = SchedulesAPI(self.http)
        self.apps = AppsAPI(self.http)
        self.docs = DocsAPI(self.http)

