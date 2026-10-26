from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import apiverve_client


class ValidatePhoneNumberTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        query = {key: tool_parameters.get(key) for key in ("number", "country",)}
        data = apiverve_client.call(self.runtime.credentials.get("api_key"), "/v1/phonenumbervalidator", query=query)
        yield self.create_json_message(data if isinstance(data, dict) else {"result": data})
