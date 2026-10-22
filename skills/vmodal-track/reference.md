# vmodal-track reference

Shared rules (spec checklist, scenes, verdicts, timestamps, frame tools) are in
[../vmodal-find/reference.md](../vmodal-find/reference.md). This file covers what tracking adds.

## Budgets

| Item | Value |
|---|---|
| text queries | 3: full, core + distinctive attribute, one rephrasing |
| image queries (identity mode) | 1, at most 2 |
| hits per query | MCP caps a call at 20 rows: `limit=20`; page 1 of each query + page 2 of the full query, then more pages (`offset` 40, 60, 80) only when all found appearances are viewed and the stop rule allows; max 5 pages per query |
| scene gap | ≤ 3 s (same as vmodal-find) |
| appearance gap | ≤ 10 s between scenes of the same video |
| second frame | last hit of a FAIL appearance spanning ≥ 5 s; vmodal-find second look for unclear PARTIALs |
| batch | 10 appearances per bulk frame fetch |
| stop | 2 batches in a row with no new PASS / SAME, or 50 appearances viewed |

## Search by image

- Tool: `search_video(group_name, stream_name?, image_query=<base64>, limit=20)`. `find` has
  no image input.
- `image_query` must be **plain base64 image bytes**. A signed URL fails with
  `400 cannot decode image_query base64: Incorrect padding`.
- Make it with `bash <skill_dir>/scripts/anchor_b64.sh <frame.png> x y w h`. Frames are
  640×360; take the box from the frame you viewed, with a small margin around the subject.
- **Crop the subject.** Tested on `city`: the whole Kyoto taxi frame (1:57) returned mostly
  the same 1:54–2:05 stretch of street. The cropped taxi also returned other Kyoto scenes
  (2:25, 2:29, 4:24, 6:14, 7:45) and two Rome videos.
- Scores from image search are a rank too: use the returned order, not the number.

## Identity labels

| Label | Rule | On the trail? |
|---|---|---|
| SAME | visible signature details all match; ≥ 1 clearly visible | yes |
| LIKELY SAME | no contradiction, key details hidden | yes, marked "likely" |
| DIFFERENT | a signature detail contradicts | footer count |
| DESCRIPTION ONLY | fits the description, nothing tells it apart | footer count |

Good signature details: plate or number, logo, text on the subject, pattern, accessory,
damage, unusual color combination. Weak ones: color alone, type alone, location.

## Worked example (identity mode)

Request: `Track the taxi with plate 50-20. Collection: city, Kyoto`

1. Anchor: `find("red taxi with a white roof", "city", "Street_Visit_in_Kyoto")` → 1:57.
   Frame shows plate 50-20, white roof light, sticker on the rear window.
2. Signature: `plate 50-20` · `white roof light` · `rear window sticker`.
3. Search: 3 `find` variants + one `search_video` with the taxi cropped at x=225 y=190 w=210 h=160.
4. Group → appearances, e.g. 1:52–2:05 (one appearance, several scenes), 3:31, 4:24.
5. Verify: 1:52–2:05 SAME (plate readable); 3:31 taxi drives past, plate not readable,
   other details don't match → DESCRIPTION ONLY or DIFFERENT, never SAME.
6. Stop after two batches with no new SAME; report the trail and the footer counts.
