from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

import apiverve_client


class ApiverveProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            apiverve_client.validate_key(credentials.get("api_key"))
        except apiverve_client.ApiverveError as error:
            raise ToolProviderCredentialValidationError(str(error)) from error
