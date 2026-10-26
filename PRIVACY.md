# APIVerve for Dify privacy policy

The plugin sends the inputs of each tool call over HTTPS to `api.apiverve.com`, together with your APIVerve API key in the `x-api-key` header. Those inputs are whatever you or your agent pass to the tool, for example an email address, phone number, IP address, domain, or the parameters given to Run API. Some catalog APIs called through Run API fetch a URL you supply, or process text, images or documents you pass in.

APIVerve processes each request to return its result and records request metadata (API name, time, status, credits used) against your account for usage reporting and billing. APIVerve's handling of request data is described in its privacy policy: https://apiverve.com/privacy.

Find APIs downloads the public API catalog from `assets.apiverve.com` and sends no user data or key.

The API key is stored by Dify as a secret provider credential. The plugin does not write the key or any tool input to files or logs, does not return the key in tool output, and refuses redirects so the key is never sent to another host. The plugin itself stores no user data; it keeps only the public catalog in memory for up to one hour.

Dify and APIVerve may process or retain information under their own policies. Privacy contact: hello@apiverve.com.
