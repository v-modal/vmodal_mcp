# vmodal-trend-radar reference

## Default items (12)

| # | Item | Kind | Notes for verification |
|---|---|---|---|
| 1 | barrel jeans | silhouette | curved, wide leg tapering at ankle; straight wide jeans fail |
| 2 | burgundy | color | on a main garment; wine/oxblood pass, red/brown fail |
| 3 | suede jacket | material | napped matte leather look; smooth leather fails |
| 4 | leopard print | print | on a garment/shoes; bag-only = PARTIAL |
| 5 | ballet flats | shoes | flat, rounded toe; loafers fail |
| 6 | trench coat | outerwear | belted / double-breasted, any color |
| 7 | long wool coat | outerwear | below the knee |
| 8 | sheer or mesh | material | see-through layer visible |
| 9 | boat shoes | shoes | moccasin stitching, laces at side |
| 10 | oversized blazer | tailoring | shoulders dropped or past hips |
| 11 | scarf as accessory | accessory | worn on bag/head/neck as styling, not winter muffler only |
| 12 | red accent | color | one small red item (bag, shoes, tights) in an otherwise neutral look |

## Collection map

| Collection | Column | Sub-collection |
|---|---|---|
| fashion_milan | summer | `Most_Iconic_Summer_Street_Fashion_in_Milan_` |
| fashion_milan | fall | `Fall_Fashion_Trends_and_Classic_Pieces_for_dressing_this_Autumn` |
| fashion_milan | winter | `Italian_Winter_Fashion_Best_Winter_Style_ideas_You_ll_want_to_recreate` |
| fashion_all | brand (optional) | `fashion_brand_milan` |

Columns are where you search; **periods** (matrix columns) come from video filenames,
e.g. `NOVEMBER_2025_…` → `2025-11`, `FASHIONABLE_OUTFITS_WINTER_2026_…` → `2026-winter`,
`Discover_Milan_s_June_Vibe…` → `summer-unknown` (no year: shown, never used for trends).
Check one with `python <skill_dir>/scripts/fashion_period.py period <filename> <sub_collection>`.

## Budgets

| What | Default | Deep run |
|---|---|---|
| items | ≤ 12 | ≤ 12 |
| scenes verified per cell | 6 | 8 |
| scenes per video per cell | 2 | 3 |
| pages per cell | 1 (+1 if < 6 scenes) | 3 |
| frames per bulk call | ≤ 20 | ≤ 20 |

12 items × 3 columns × 6 = 216 frames max; tell the user when a run will exceed ~100 frames
and offer to start with 4 items.

## Thresholds (in `scripts/trend_matrix.py`)

`MIN_VIEWED=4`, `MIN_PERIODS=3`, `DELTA=0.15`, `EVERGREEN=0.5`, `N_EVIDENCE=3`.
Rates are PASS / viewed among the scenes search surfaced for that item, so they compare
periods for the same item; they are not prevalence in the population.

## Worked example (shape; counts are illustrative)

`suede jacket`, fall column: 20 hits → 9 scenes → top 6 (≤ 2 per video) → frames: 4 PASS,
1 PARTIAL (jacket hidden by bag), 1 FAIL (smooth leather). The 6 lines go into
`verdicts.jsonl`; the script spreads them across `2025-09` and `2025-11` by filename.

## Tests

`python skills/vmodal-trend-radar/tests/test_trend_matrix.py test_all`
