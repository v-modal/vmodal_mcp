> ### Get a free beta API key
>
> Join the V-Modal beta by [filling out the contact form](https://v-modal.com/page/contact.ts).

# vmodal MCP

Use the vmodal video and image API from Claude Code, Codex, Cursor, GitHub
Copilot, or any client that supports local MCP servers.

## Requirements

- Python 3.10 or newer
- A vmodal API key

## Install

Install the latest public release from GitHub:

```bash
python -m pip install --upgrade "git+https://github.com/v-modal/vmodal_mcp.git@main"
```

Check that the command is available:

```bash
vmodal-mcp --help
```

## Configure your MCP client

Replace `PUT_API_KEY_HERE` with your vmodal API key. The server needs no other
public configuration.

### Claude Code

```bash
claude mcp add --scope user vmodal \
  -e api_key=PUT_API_KEY_HERE -- \
  vmodal-mcp run --transport stdio

claude mcp list
```

### Codex

```bash
codex mcp add --env api_key=PUT_API_KEY_HERE vmodal -- \
  vmodal-mcp run --transport stdio

codex mcp list
```

### Cursor and other JSON-based clients

Add this server to your client's MCP configuration:

```json
{
  "mcpServers": {
    "vmodal": {
      "command": "vmodal-mcp",
      "args": ["run", "--transport", "stdio"],
      "env": {
        "api_key": "PUT_API_KEY_HERE"
      }
    }
  }
}
```

For Cursor, save it as `.cursor/mcp.json` for the current project or
`~/.cursor/mcp.json` for all projects. Do not commit a real API key.

## Basic usage

Restart your MCP client after adding the server. You can then ask your assistant:

```text
Call the vmodal health tool, then call auth_me.
```

A successful `auth_me` result confirms that the API key is connected to your
account. Other common requests include:

```text
List my vmodal collection groups.
Search my videos for "a person walking near the ocean".
Upload ./demo.mp4 to my demo collection.
```

The client will show the exact tool inputs and ask for any missing values.

## Troubleshooting

- `vmodal-mcp: command not found`: restart the client after installation and
  ensure the scripts directory printed by
  `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"` is on
  your `PATH`.
- `401`: the API key is missing, invalid, or expired.
- `403`: the API key is valid but does not have permission for that operation.
- Server changes are not visible: restart the MCP client so it reconnects.

Run the server directly for a quick startup check:

```bash
vmodal-mcp run --transport stdio
```
