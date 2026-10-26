from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import apiverve_client


class FindApisTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        limit = int(tool_parameters.get("limit") or 10)
        matches = apiverve_client.search(tool_parameters.get("query"), max(1, min(limit, 25)))
        yield self.create_json_message({"apis": matches})
