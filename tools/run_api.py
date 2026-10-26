import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import apiverve_client


class RunApiTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        raw = tool_parameters.get("parameters")
        if isinstance(raw, dict):
            params = raw
        elif raw:
            try:
                params = json.loads(raw)
            except ValueError:
                raise apiverve_client.ApiverveError('Parameters must be a JSON object, for example {"domain": "example.com"}.')
            if not isinstance(params, dict):
                raise apiverve_client.ApiverveError("Parameters must be a JSON object.")
        else:
            params = {}
        data = apiverve_client.run(self.runtime.credentials.get("api_key"), tool_parameters.get("api"), params)
        yield self.create_json_message(data if isinstance(data, dict) else {"result": data})
