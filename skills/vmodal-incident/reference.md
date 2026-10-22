# vmodal-incident reference

Shared rules (spec checklist, scenes, frame tools, timestamps) are in
[../vmodal-find/reference.md](../vmodal-find/reference.md). This file covers what incidents add.

## Budgets

| Item | Value |
|---|---|
| search phrases | the catalog's 2 phrases per type in scope |
| hits per query | `limit=50` (older MCP: `limit=20` + `offset=20`) |
| scene gap / candidate gap / candidate length | ≤ 3 s / ≤ 10 s / ≤ 15 s, same video |
| triage | 10 candidates per batch, one contact sheet per batch |
| triage stop | 2 batches in a row with no new PASS, or 30 candidates viewed |
| rebuilds | all PASS, then PARTIAL by rank; at most 6 per run |
| timeline window | peak − 4 s … peak + 4 s, 1 s steps (9 records, one contact sheet) |
| extension | ± 5 … 8 s once per side when the peak is at an edge or followed by gaps; at most 2 per candidate |
| full-size views | the peak, plus the trigger when a signal or lane line decides the type |
| download | ≤ 20 records per call |

## Incident catalog

For each type: the words that select it, two `find` phrases (deliberately different, so
they don't return the same list), the checklist line shown to the user, the triage rule,
type rules for the verdict, and what never goes in a timeline.

Never confirmable for **every** type: fault, intent, sound (horn, shouting), speed not
shown on an overlay, braking unless brake lights are visible.

In scan mode one candidate can fit several types: report the most serious (collision >
near-miss > pedestrian / cyclist conflict > red-light running > lane change) and mention
the others in its "What is seen".

### Near-miss (vehicles)

- **Request words**: near-miss, close call, almost hit, swerve.
- **Phrases**: "car swerves in front of the dashcam car" · "two cars almost collide on the road".
- **Checklist**: vehicle (core) · in our lane or path (attribute) · about one car length or closer (attribute) · no contact (attribute)
- **PASS in triage**: another vehicle in our lane or crossing our path at about one car
  length or less.
- **Rules**: if contact is seen, it's a collision instead. Distance is "about N car
  lengths", never metres.
- **Never confirmable**: exact distance.

### Collision

- **Request words**: crash, collision, accident, hit, rear-end.
- **Phrases**: "car crash collision" · "damaged car stopped at an angle after an accident".
- **Checklist**: vehicle (core) · contact or damage (attribute) · on the road (context)
- **PASS in triage**: contact, visible damage, debris, or a vehicle stopped at an odd angle.
- **Rules**: contact seen in no frame but damage after → peak Low ("contact between
  frames") and POSSIBLE, unless damage shows in two or more frames right after the peak
  (then CONFIRMED, peak Medium).
- **Never confirmable**: force, injuries.

### Red-light running

- **Request words**: red light, ran the light, signal, intersection.
- **Phrases**: "car running a red light at an intersection" · "vehicle in the middle of a junction while cross traffic waits".
- **Checklist**: vehicle (core) · signal facing that vehicle red (attribute) · vehicle past the stop line / entering the junction (attribute)
- **PASS in triage**: a red signal facing a vehicle **and** that vehicle past the stop
  line or moving into the junction. Vehicles stopped or queued at a red are **FAIL**.
- **Rules**:
  - The vehicle can be another car or the dashcam car itself; say which.
  - A red ball with a lit green arrow: a vehicle turning in the arrow's direction is
    **not** running the red.
  - "Entering" means crossing the stop line or the near edge of the junction in a frame.
    If that crossing falls in a gap or past a cut, the verdict is at most POSSIBLE.
  - No red signal visible in any kept frame → at most POSSIBLE, "signal not visible".
- **Never confirmable**: which signal applies when several are visible; signal timing.

### Pedestrian / cyclist conflict

- **Request words**: pedestrian, person, walker, cyclist, bike, stepped out.
- **Phrases**: "pedestrian crossing in front of the car" · "cyclist riding in the traffic lane ahead".
- **Checklist**: pedestrian or cyclist (core) · in the roadway (attribute) · in or entering the car's path (attribute)
- **PASS in triage**: a person or cyclist in the roadway in or entering a vehicle's path
  at short range, or people down on the road.
- **Rules**: a request for pedestrians only still includes cyclists; label the incident
  "cyclist" so the user can tell. Third-party events (people falling, colliding with each
  other next to our lane) count; at night, their position against the lane edge is
  Medium at best.
- **Never confirmable**: whether anyone braked.

### Unsafe lane change / cut-off

- **Request words**: cut off, cut in, lane change, merge, swerved into our lane.
- **Phrases**: "car changing lanes suddenly in front" · "vehicle merging into the lane very close ahead".
- **Checklist**: vehicle (core) · crosses a lane line (attribute) · close in front (attribute)
- **PASS in triage**: a vehicle across a lane line, close in front.
- **Rules**: the crossing must show in two frames (on the line, then in our lane) for
  High.
- **Never confirmable**: indicator use (unless a lit indicator is visible).

## Frames and timestamps

- `dashcam_v1` (tested 2026-10-13): one sub-collection `astream`, index v0, one ~11 min
  compilation video (`Dash_Cam_Owners_Australia_April_2026_On_the_Road_Compilation`).
- Frames are on whole seconds, at most one per second, but **many seconds are not
  indexed**: 11 of 36 window seconds in one test, 1:27–1:36 entirely. A missing second
  returns `found: false`, `error: "image not found"`; pass `-` to `frames_strip.sh` so
  the tiles still line up with the seconds.
- Any indexed second can be fetched, not only search hits: copy a hit's row and change
  `ts_unix_13digits`.
- Compilations cut often: 3 of 4 rebuilt windows in one test held a cut (end-card
  montage, car park → junction, a different clip). Use the overlay clock to tell.
- Downloads: see SKILL.md "Downloading frames". With the old bulk tool, files are named
  `astream_<i>_<hash>.webp`; the time isn't in the name, and a call over 20 URLs skips
  the rest silently (`skipped` > 0).

## Contact sheet

`frames_strip.sh <out.png> <frame|->...`: up to 12 frames, 3 per row, 320×180 tiles,
left to right then top to bottom. Tile `n` is the n-th argument. A 9-second window is a
3×3 grid: row 1 = peak − 4 … − 2, row 2 = peak − 1 … + 1 (centre tile = peak), row 3 =
peak + 2 … + 4. A triage batch of 10 is a 3-3-3-1 grid, tile n = candidate n. Needs `ffmpeg` (sheet) plus a WebP converter (`sips`, `dwebp`, `ffmpeg`).

## Worked example (NOT AN INCIDENT)

Request: `Find near-misses. Collection: dashcam_v1`.

1. Search returns a cluster at 5:16–5:23 for "near miss" and "crash" phrases alike.
2. Triage frame 5:20: wide highway, dark hatchback close in the left lane, a car carrier
   on the right shoulder → PARTIAL (vehicle close, conflict unclear) → rebuild.
3. Window 5:17–5:25: 5:24 and 5:25 not found → `-`. Sheet tiles:
   - 5:17–5:22: same highway; the overlay reads 34 → 63 km/h and 03:14:32 → 03:14:37.
     A motorcyclist in a hi-vis vest is next to the car carrier on the right at 5:18; the
     hatchback stays in its own lane on the left, growing closer as we pass.
   - 5:23: a different road (cloudy junction, different overlay) → **clip cut**; dropped.
4. No vehicle enters our lane, no person in our path → **NOT AN INCIDENT**. It goes in the
   footer count only. If the peak had been at 5:22, it would be "1 s before a cut" and at
   most POSSIBLE.

## Worked example (CONFIRMED, third parties)

Request: `Find near-misses with pedestrians. Collection: dashcam_v1` (tested 2026-10-13).

1. Triage: a candidate at 1:18–1:26 shows only a distant cyclist (PARTIAL); a second one
   at 1:37–1:38 shows a bicycle on the road. Both are rebuilt.
2. Window 1:18–1:26 at night (1:19 and 1:24 not indexed): a cyclist with a red tail light
   at the right edge of our lane gets closer; overlay speed falls 43 → 15 → 11 km/h.
   1:25: hi-vis cyclist about one car length ahead at the edge line, a second person
   next to them. 1:26 (peak): both people down on the road, bicycle lying in the roadway.
3. The peak is at the window's edge, so it's extended: 1:27–1:36 are all not indexed.
   1:37–1:38 are found; the overlay clock (21:07:50 → 21:08:02, no jump) shows the same
   clip, so the two candidates are one incident. Outcome: dashcam car stopped (0 km/h),
   one person standing over the bike.
4. Verdict **CONFIRMED** (trigger High over 1:20–1:23, peak Medium: night, position at
   the lane edge hard to judge). Labelled "cyclist", "third parties; no contact with the
   dashcam car seen". Not determinable: whether the two people collided or one fell
   (between frames), fault, braking.
