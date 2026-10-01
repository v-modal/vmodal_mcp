<div align="center">
  <img src="https://raw.githubusercontent.com/v-modal/vmodal_mcp/main/readme_assets/logo_vmodal_owl_v.jpeg" alt="VModal owl" width="88">
  <h1>VModal MCP</h1>
  <p><strong>Search, upload, and organize videos with your AI assistant.</strong></p>
  <p>Works with Claude Code, Codex, Cursor, and GitHub Copilot.</p>
</div>

<br>

<img src="https://raw.githubusercontent.com/v-modal/vmodal_mcp/main/readme_assets/dev_homepage.jpg" alt="A searchable wall of video and image moments" width="100%">

## Quick start

You need Python 3.10 or newer and a VModal API key.


### 0. Get a free API key by signing up at:
  [VModal API KEY page](https://v-modal.com/page/contact.ts).


### 1. Install VModal MCP
```bash
python -m pip install --upgrade "git+https://github.com/v-modal/vmodal_mcp.git@main"
```

### 2. Run the simple test

Replace `PUT_API_KEY_HERE` with your API key:

```bash
export VMODAL_API_KEY=PUT_API_KEY_HERE
vmodal test
```

The first `vmodal` command copies the package's complete `assets/` folder to
`./assets/` in the folder where you run it. The test uses
`./assets/test_video_20_frames.mp4`, uploads the video, creates an index, waits
until the index is ready, and runs a search. It normally takes about one minute.
A successful run starts with `ok: true`.


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
```
Use VModal MCP to check the service health, then show my account profile.

Then, use VMODAL MCP to run test



```
If both calls succeed, setup is complete.



## Copy Paste these prompts
```
### Run the initial test with the included asset

Use the test video at `./assets/test_video_20_frames.mp4`. Upload it to a new
test collection, create the index, wait until indexing finishes, then search
for “colorful test pattern.” Confirm that upload, indexing, and search all
succeeded.



### Upload and search a video

Upload `./my_video.mp4` to a collection named `my_videos`. Create the index,
wait until it is ready, then search for “a person walking outside.”


---
### Search existing videos

Search my videos for “a red car.” Show the best three matching frames.


---
### Upload a folder

Upload all MP4 files from `./camera_exports` to a collection named
`camera_exports`. Tell me which files succeeded.


---
### Check usage

Show my current VModal usage and explain it simply.
```


## Quick fixes

- `vmodal` or `vmodal-mcp` is not found: restart the terminal after installing.
- `401`: check that the API key is correct and has not expired.
- VModal tools do not appear: restart Claude, Codex, Cursor, or Copilot.
- To rerun the full setup test: run `vmodal test` again. It creates a new test
  collection each time.

Keep your API key private and never commit it to a repository.


## Public MCP operations

Each prompt below maps to one public VModal MCP tool. Replace the example
values with your own paths, collection names, IDs, filenames, or URLs.
```
1. **Check service health — `health`**

   > Use VModal MCP to check the gateway and API health, then report the service version and status.

2. **Show the current account — `auth_me`**

   > Use VModal MCP to show the account profile associated with my current API key.

3. **Search videos and images — `search_video`**

   > Use VModal MCP to search all streams in collection `my_videos` for “a person walking outside”; return the five best matching image frames.

   `group_name` (the collection name) is required. Omitting `stream_name` searches
   all streams. Image search uses index version 0 by default; if the collection's
   image index uses another version, pass `version_lancedb` explicitly.

4. **List collection groups — `collection_groups_list`**

   > Use VModal MCP to list all collection groups available for mode `vid_file`.

5. **Upload one video or image — `collection_video_upload`**

   > Use VModal MCP to upload `./video.mp4` to collection `my_videos`, stream `astream`, using mode `vid_file` and modality `vid_raw`.

6. **Upload a folder of videos — `collection_video_upload_bulk`**

   > Use VModal MCP to upload all MP4 files from `./camera_exports` to collection `camera_exports`, stream `astream`, and report every successful or failed file.

7. **Upload metadata — `collection_upload_metadata`**

   > Use VModal MCP to upload metadata from `./metadata.jsonl` for group `my_images`, stream `astream`, using mode `img_file` and append write mode.

8. **Update collection metadata — `collection_description_update`**

   > Use VModal MCP to update `video.mp4` in collection `my_videos`, stream `astream`, mode `vid_file`, with description “Outdoor walking sequence” and tags `outdoor` and `walking`.

9. **Delete a collection scope — `collection_delete`**

   > Use VModal MCP to dry-run deletion of collection `old_videos` in mode `vid_file`; show everything that would be removed and wait for my confirmation before performing the deletion.

10. **Add assets to a collection — `collection_add_assets`**

    > Use VModal MCP to add asset IDs `asset_001` and `asset_002` to collection ID `collection_001`, group `my_images`, stream `astream`, using mode `img_file`.

11. **List indexing jobs — `index_jobs_list`**

    > Use VModal MCP to list the 20 most recent indexing jobs for collection `my_videos`, including each job ID and status.

12. **Create an index — `index_create`**

    > Use VModal MCP to create a `vid_img_emb` index for collection `my_videos`, stream `astream`, using mode `vid_file`; return the new job ID.

13. **Check indexing status — `index_status`**

    > Use VModal MCP to check indexing job `JOB_ID` and summarize its status, progress, indexed frame count, and any error.

14. **Delete an index — `index_delete`**

    > Use VModal MCP to dry-run deletion of index version `VERSION` for collection `my_videos` in mode `vid_file`; show what would be removed and wait for my confirmation before deleting it.

15. **Show user statistics — `admin_user_stats`**

    > Use VModal MCP to fetch my available user statistics and summarize the counters and totals.

16. **Show usage details — `admin_usage`**

    > Use VModal MCP to show my API usage for `YYYY-MM-DD` and summarize the main usage categories.

17. **Show authentication cache statistics — `admin_cache_stats`**

    > Use VModal MCP to fetch my authentication and cache statistics, then explain the results briefly.


```
