# APIVerve for Dify

APIVerve gives you several hundred ready-to-use APIs behind one key. This plugin brings them to Dify agents, chatflows and workflows.

**Author:** apiverve · **Version:** 0.1.0 · **Type:** tool · **Source:** https://github.com/apiverve/dify-plugin

## Tools

| Tool | What it does |
|---|---|
| Validate Email | Syntax, MX and SMTP deliverability, disposable and free-provider flags, typo suggestions |
| Validate Phone Number | Validity, line type, country, E.164 and international formats |
| Look Up IP Address | Country, region, city, coordinates and timezone of an IP |
| Look Up DNS Records | A, AAAA, MX, NS, TXT, CNAME and SOA records of a domain |
| Check SSL Certificate | Issuer, validity dates and days until expiry |
| Get Exchange Rate | Rate between two currencies, latest or on a past date |
| Find APIs | Search the APIVerve catalog by keyword; returns each API's id and parameters (no credits used) |
| Run API | Call any API in the catalog by id, with its parameters as a JSON object |

Find APIs and Run API work together: an agent searches the catalog, picks an API, then calls it. For example, Find APIs with `whois` returns `whoislookup` and its `domain` parameter, and Run API with `api = whoislookup` and `parameters = {"domain": "example.com"}` returns the record.

## Setup

1. Create a free account at [apiverve.com](https://apiverve.com) and copy your API key from the [dashboard](https://dashboard.apiverve.com).
2. In Dify, install **APIVerve** from the Marketplace.
3. Open **Tools → APIVerve → Authorize**, paste the key and save. The key is checked against your account; the check uses no credits.
4. Add any APIVerve tool to an agent, chatflow or workflow.

## Requirements

- An APIVerve API key. Each call uses the credits shown on the API's page; the free plan includes a monthly allowance.
- Network connection: outbound HTTPS from the Dify plugin runtime to the APIVerve endpoints `api.apiverve.com` and `assets.apiverve.com`. No other host is contacted.

## Errors

| Message | Meaning |
|---|---|
| APIVerve rejected the API key | The key is wrong or was deleted. Re-authorize with a current key. |
| This API key is not allowed to make this call | The key is scoped to other APIs or IPs, or was revoked. |
| Rate limit reached or monthly credits used up | Retry shortly, or upgrade the plan. |
| Unknown APIVerve API | The id passed to Run API is not in the catalog. Use Find APIs. |

## Links

- Documentation: https://docs.apiverve.com
- API catalog: https://apiverve.com/marketplace
- Support: hello@apiverve.com
- Privacy: [PRIVACY.md](PRIVACY.md)
