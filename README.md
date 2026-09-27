<div align="center">
  <img src="https://raw.githubusercontent.com/v-modal/vmodal_mcp/main/readme_assets/logo_vmodal_owl_v.jpeg" alt="VModal owl" width="88">
  <h1>VModal MCP</h1>
  <p><strong>Search, upload, and organize videos with your AI assistant.</strong></p>
  <p>Works with Claude Code, Codex, Cursor, and GitHub Copilot.</p>
</div>

<br>

<img src="https://raw.githubusercontent.com/v-modal/vmodal_mcp/main/readme_assets/dev_homepage.jpg" alt="A searchable wall of video and image moments" width="100%">

## Quick start

You need Python 3.10 or newer and a VModal API key. You can request access from
the [VModal contact page](https://v-modal.com/page/contact.ts).

### 1. Install VModal MCP

```bash
python -m pip install --upgrade "git+https://github.com/v-modal/vmodal_mcp.git@main"
```

### 2. Run the simple test

Replace `PUT_API_KEY_HERE` with your API key:

```bash
export api_key=PUT_API_KEY_HERE
vmodal test
```

This uses the included 20-frame test video. It uploads the video, creates an
index, waits until the index is ready, and runs a search. It normally takes
about one minute. A successful run starts with `ok: true`.

### 3. Connect your AI assistant

Choose the command for your editor and replace `PUT_API_KEY_HERE`.

#### Claude Code

```bash
claude mcp add --scope user vmodal \
  -e api_key=PUT_API_KEY_HERE -- \
  vmodal-mcp run --transport stdio

claude mcp list
```

#### Codex

```bash
codex mcp add --env api_key=PUT_API_KEY_HERE vmodal -- \
  vmodal-mcp run --transport stdio

codex mcp list
```

#### GitHub Copilot CLI

```bash
copilot mcp add vmodal --env api_key=PUT_API_KEY_HERE -- \
  vmodal-mcp run --transport stdio

copilot mcp list
```

#### Cursor

Save this as `.cursor/mcp.json`:

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

Restart your editor after connecting VModal.

### 4. Check the connection

Ask your assistant:

> Use VModal to check the service health, then show my account profile.

If both calls succeed, setup is complete.

## Try these prompts

### Run the initial test with the included asset

> Use the test video in `uinterface/mcp_python/src/mcp_server/assets`. Upload it
> to a new test collection, create the index, wait until indexing finishes, then
> search for “colorful test pattern.” Confirm that upload, indexing, and search
> all succeeded.

### Upload and search a video

> Upload `./my_video.mp4` to a collection named `my_videos`. Create the index,
> wait until it is ready, then search for “a person walking outside.”

### Search existing videos

> Search my videos for “a red car.” Show the best three matching frames.

### Upload a folder

> Upload all MP4 files from `./camera_exports` to a collection named
> `camera_exports`. Tell me which files succeeded.

### Check usage

> Show my current VModal usage and explain it simply.

## Quick fixes

- `vmodal` or `vmodal-mcp` is not found: restart the terminal after installing.
- `401`: check that the API key is correct and has not expired.
- VModal tools do not appear: restart Claude, Codex, Cursor, or Copilot.
- To rerun the full setup test: run `vmodal test` again. It creates a new test
  collection each time.

Keep your API key private and never commit it to a repository.
