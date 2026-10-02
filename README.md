<div align="center">
  <img src="https://raw.githubusercontent.com/v-modal/vmodal_mcp/main/readme_assets/logo_vmodal_owl_v.jpeg" alt="VModal owl" width="88">
  <h1>VModal MCP</h1>
  <p><strong>Find moments in your videos by asking your AI assistant.</strong></p>
  <p>Works with Claude Code, Codex, Cursor, and GitHub Copilot.</p>
</div>

<br>

<img src="https://raw.githubusercontent.com/v-modal/vmodal_mcp/main/readme_assets/dev_homepage.jpg" alt="A searchable wall of video and image moments" width="100%">

After setup, just ask:

```text
Find a red car in my city collection.
```

A **collection** is a group of your videos or images. A **sub-collection** is
a smaller group inside it. You can search a whole collection without choosing
a sub-collection. VModal chooses the search index version automatically.

## Set up once

You need Python 3.10 or newer and an AI assistant from the list above.
Run the setup commands in your terminal. After setup, type the prompts in your
assistant's chat.

### 1. Get your API key

[Sign up for a VModal API key](https://v-modal.com/page/contact.ts).
Copy your key. Wherever you see `PUT_API_KEY_HERE` below, replace it with your
key. Keep your key private.

### 2. Install VModal

Copy this command into your terminal:

```bash
python -m pip install --upgrade "git+https://github.com/v-modal/vmodal_mcp.git@main"
```

### 3. Connect your assistant

Follow **only the instructions for your assistant**.

#### Claude Code

Paste this into your terminal after replacing `PUT_API_KEY_HERE`:

```bash
claude mcp add --scope user vmodal \
  -e api_key=PUT_API_KEY_HERE -- \
  vmodal-mcp run --transport stdio
```

#### Codex

Paste this into your terminal after replacing `PUT_API_KEY_HERE`:

```bash
codex mcp add --env api_key=PUT_API_KEY_HERE vmodal -- \
  vmodal-mcp run --transport stdio
```

#### GitHub Copilot CLI

Paste this into your terminal after replacing `PUT_API_KEY_HERE`:

```bash
copilot mcp add vmodal --env api_key=PUT_API_KEY_HERE -- \
  vmodal-mcp run --transport stdio
```

#### Cursor

In your project, create a file named `.cursor/mcp.json`. Paste the following
into it, replace `PUT_API_KEY_HERE` with your key, and save:

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

### 4. Restart your assistant and check the connection

Open a new chat and paste:

```text
Use VModal to check my connection and show my account.
```

If your assistant shows your account, you're ready.

## Start here: copy a prompt into chat

### See your collections

```text
List all my collections.
```

### See your sub-collections

```text
List all my sub-collections in a table with two columns:
Collection | Sub-collection
```

### Find something

Replace `city` with a collection name from your list:

```text
Find a red car.
Collection: city
```

This searches the whole collection. To search one sub-collection, add its name:

```text
Find a red car.
Collection: city
Sub-collection: rome
```

### Get the matching pictures

```text
Find a red car in my city collection. Save the best three matching
pictures to my computer and tell me where to find them.
```

### Upload your first video

Replace `./my_video.mp4` with the path to a video on your computer:

```text
Upload ./my_video.mp4 to a collection named my_videos, in a sub-collection
named my_uploads. Make it searchable, wait until it's ready, then find
a person walking outside.
```

[More ready-to-copy prompts →](prompts.md)

## Try it with a sample video (optional)

Run these commands in your terminal, with your API key:

```bash
export VMODAL_API_KEY=PUT_API_KEY_HERE
vmodal test
```

This uploads an included sample video, makes it searchable, and runs a search.
It usually takes about a minute. Look for `ok: true` in the result.
Each run creates a new test collection.

## Need help?

- **VModal doesn't appear in your assistant:** restart your assistant and open a new chat.
- **Your API key is rejected, or you see `401`:** check the key you entered in step 3.
- **`vmodal-mcp` or `vmodal` is not found:** restart your terminal and retry. If it still fails, repeat step 2 using the Python installation your terminal uses.
- **No matches:** ask your assistant to list your collections, check the collection name, and try a simpler description. If you just uploaded a video, ask whether it is ready to search.

For developer details, see the [tool contract](docs/tool_contract.md).
