## vibe-mcp-client

[vibe coding](https://x.com/karpathy/status/1886192184808149383?lang=en) an mcp client

**setup**

```bash
# clone
git clone https://github.com/DevPranjal/vibe-mcp-client.git
cd vibe-mcp-client

# install uv (for windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# initialize
uv init
uv add mcp[cli] openai markdown pillow requests tkhtmlview
uv run mcp
```

create a `.env` file with the following fields:

```
BING_SEARCH_API_KEY=
AZURE_MAPS_API_KEY=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
```

```bash
# set environment variables and start client
uv run main.py
```

**tools available currently** -

- `bing_search(query, count)`
- `get_travel_time(origin, destination, mode)`
- `find_hotels(address, radius_km, limit)`

for more tools, add to [server.py](./server.py)
