"""Fixed-host HTTPS transport for api.apiverve.com and the public API catalog."""

import json
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_BASE = "https://api.apiverve.com"
CATALOG_URL = "https://assets.apiverve.com/cli-manifest.json"
ACCOUNT_PATH = "/v1/analytics/account"
PLUGIN_VERSION = "0.1.0"
USER_AGENT = f"apiverve-dify/{PLUGIN_VERSION}"
TIMEOUT_SECONDS = 60
CATALOG_TTL_SECONDS = 3600


class ApiverveError(Exception):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open(request):
    # The key is only ever sent to API_BASE; never follow a redirect elsewhere.
    return build_opener(_NoRedirect()).open(request, timeout=TIMEOUT_SECONDS)


def _redact(value, secret):
    if isinstance(value, str):
        return value.replace(secret, "[redacted]") if secret else value
    if isinstance(value, list):
        return [_redact(item, secret) for item in value]
    if isinstance(value, dict):
        return {_redact(k, secret): _redact(v, secret) for k, v in value.items()}
    return value


def _error_message(status, payload):
    detail = None
    if isinstance(payload, dict):
        detail = payload.get("error") or payload.get("message")
    if status == 401:
        return "APIVerve rejected the API key. Check the key in the APIVerve credential."
    if status == 403:
        return f"This API key is not allowed to make this call{': ' + detail if detail else '.'}"
    if status == 429:
        return "Rate limit reached or monthly credits used up. Retry shortly, or upgrade your plan at https://dashboard.apiverve.com."
    if detail:
        return f"APIVerve returned {status}: {detail}"
    return f"APIVerve returned HTTP {status}."


def _to_query_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ",".join(_to_query_value(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def clean(params):
    return {k: v for k, v in (params or {}).items() if v is not None and v != ""}


def call(api_key, path, method="GET", query=None, body=None):
    """Call one APIVerve endpoint and return its `data` payload."""
    if not isinstance(api_key, str) or not api_key.strip():
        raise ApiverveError("Add your APIVerve API key in the plugin credential.")
    if not path.startswith("/v1/"):
        raise ApiverveError("Invalid APIVerve path.")
    url = API_BASE + quote(path, safe="/")
    query = clean(query)
    if query:
        url += "?" + urlencode({k: _to_query_value(v) for k, v in query.items()})
    headers = {"x-api-key": api_key.strip(), "User-Agent": USER_AGENT, "Accept": "application/json"}
    data = None
    if method == "POST":
        headers["Content-Type"] = "application/json"
        data = json.dumps(clean(body), ensure_ascii=False).encode("utf-8")
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with _open(request) as response:
            status = response.status
            payload = json.load(response)
    except HTTPError as error:
        status = error.code
        try:
            payload = json.load(error)
        except (ValueError, UnicodeError):
            payload = None
        finally:
            error.close()
    except (URLError, TimeoutError, OSError):
        raise ApiverveError("APIVerve could not be reached. Retry in a moment.")
    except (ValueError, UnicodeError):
        raise ApiverveError("APIVerve returned an unreadable response.")

    if not 200 <= status < 300:
        raise ApiverveError(_redact(_error_message(status, payload), api_key))
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise ApiverveError(_redact(_error_message(status, payload), api_key))
    result = payload.get("data", payload) if isinstance(payload, dict) else payload
    return _redact(result, api_key)


def validate_key(api_key):
    # Account analytics answers 200 for any valid key and costs no credits.
    call(api_key, ACCOUNT_PATH)


_catalog = None
_catalog_at = 0.0
_catalog_lock = threading.Lock()


def catalog():
    """Return {api_id: definition} from the public catalog, cached for an hour."""
    global _catalog, _catalog_at
    with _catalog_lock:
        if _catalog is not None and time.time() - _catalog_at < CATALOG_TTL_SECONDS:
            return _catalog
        request = Request(CATALOG_URL, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with _open(request) as response:
                apis = json.load(response)["apis"]
        except Exception:
            if _catalog is not None:
                return _catalog
            raise ApiverveError("The APIVerve catalog could not be loaded. Retry in a moment.")
        _catalog, _catalog_at = apis, time.time()
        return _catalog


def search(query, limit=10):
    """Rank catalog APIs against a free-text query."""
    words = [w for w in (query or "").lower().split() if w]
    scored = []
    for api_id, api in catalog().items():
        title = (api.get("title") or "").lower()
        category = (api.get("category") or "").lower()
        description = (api.get("description") or "").lower()
        score = 0
        for word in words:
            # Word-start matches, so "vat" finds VAT Rates but not Gravatar.
            starts = re.compile(r"\b" + re.escape(word))
            if api_id.startswith(word) or (len(word) >= 4 and word in api_id):
                score += 4
            if starts.search(title):
                score += 4
            if starts.search(category):
                score += 2
            if starts.search(description):
                score += 1
        if score or not words:
            scored.append((score, api_id, api))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [describe(api_id, api) for _, api_id, api in scored[:limit]]


def describe(api_id, api):
    return {
        "api": api_id,
        "title": api.get("title"),
        "category": api.get("category"),
        "description": api.get("description"),
        "parameters": [
            {
                "name": p.get("name"),
                "type": p.get("type"),
                "required": bool(p.get("required")),
                "description": p.get("description"),
                "example": p.get("example"),
            }
            for p in api.get("params", [])
        ],
    }


def run(api_key, api_id, params):
    """Call any catalog API by id, placing each parameter where the API expects it."""
    apis = catalog()
    api_id = (api_id or "").strip().lower()
    api = apis.get(api_id)
    if api is None:
        raise ApiverveError(f'Unknown APIVerve API "{api_id}". Use Find APIs to look up the API id.')
    params = clean(params)
    declared = {p["name"]: p for p in api.get("params", [])}
    missing = [name for name, p in declared.items() if p.get("required") and name not in params]
    if missing:
        raise ApiverveError(f"{api_id} needs: {', '.join(missing)}.")
    method = (api.get("method") or "GET").upper()
    query, body = {}, {}
    for name, value in params.items():
        location = declared.get(name, {}).get("in")
        if location == "query" or (location is None and method == "GET"):
            query[name] = value
        else:
            body[name] = value
    return call(api_key, api["path"], method=method, query=query, body=body if method == "POST" else None)
