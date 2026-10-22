"""python skills/vmodal-trend-radar/tests/test_trend_matrix.py test_all"""
from typing import List, Dict, Tuple, Optional, Any, Union
import os, sys, json
dirtest = "ztmp/ztests"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from fashion_period import period_parse, period_sort
from trend_matrix import matrix_build, md_matrix, build, trend_label

# real fashion_milan filenames / sub-collections
W = "Italian_Winter_Fashion_Best_Winter_Style_ideas_You_ll_want_to_recreate"
F = "Fall_Fashion_Trends_and_Classic_Pieces_for_dressing_this_Autumn"
S = "Most_Iconic_Summer_Street_Fashion_in_Milan_"
V25_02 = "FEBRUARY_2025_ULTIMATE_MILAN_STREET_STYLE_Mid_Winter_Fashion_Trends_2025_You_Need_to_See_vogue"
V25_11 = "NOVEMBER_2025_MILAN_SHOPPING_VLOG_ITALIAN_AUTUMN_STREET_STYLE_whatarepeoplewearing"
V26_02 = "FEBRUARY_2026_STYLISH_PEOPLE_IN_MILAN_FASHION_WEEK_2026_SPRING_2026_WARDROBE_SHOPPING_"
V26_W = "FASHIONABLE_OUTFITS_WINTER_2026_7_MILAN_STREET_STYLE_MILAN_SHOPPING_vogue"
V_JUNE = "Discover_Milan_s_June_Vibe_with_Italian_Street_Style_Summer_Outfits_nyfw_lfw_streetfashion"
V_DEC = "December_Street_Style_The_magic_Christmas_Atmosphere_whatarepeoplewearing_voguejapan"


def fake_verdicts() -> List[Dict]:
    """item -> [(filename, stream, n_pass, n_viewed)]"""
    plan = {
        "suede jacket":   [(V25_02, W, 1, 4), (V25_11, F, 2, 4), (V26_02, W, 4, 4)],  # rising
        "long wool coat": [(V25_02, W, 3, 4), (V25_11, F, 4, 4), (V26_02, W, 3, 4)],  # evergreen
        "leopard print":  [(V25_02, W, 3, 4), (V25_11, F, 1, 4), (V26_02, W, 0, 4)],  # fading
        "ballet flats":   [(V_JUNE, S, 2, 2)],                                        # insufficient
    }
    rows = []
    for item, cells in plan.items():
        for fn, st, npass, nview in cells:
            for i in range(nview):
                rows.append({"item": item, "stream_name": st, "filename": fn,
                             "ts_start_ms": 10000 * i, "ts_end_ms": 10000 * i + 3000,
                             "verdict": "PASS" if i < npass else "FAIL", "evidence": "",
                             "frame_png": f"/tmp/{item[:4]}_{fn[:8]}_{i}.png"})
    return rows


def test1():
    """period parse on real filenames"""
    p = period_parse(V25_02, W)
    assert p == {"season": "winter", "month": 2, "year": 2025, "period_key": "2025-02"}
    assert period_parse(V25_11, F)["period_key"] == "2025-11"
    assert period_parse(V25_11, F)["season"] == "fall"
    # month wins over the SPRING token in the title
    assert period_parse(V26_02, W)["season"] == "winter"
    assert period_parse(V26_W, W)["period_key"] == "2026-winter"


def test2():
    """no year -> season-unknown; season from month, else stream"""
    assert period_parse(V_JUNE, S)["period_key"] == "summer-unknown"
    assert period_parse(V_DEC, W) == {"season": "winter", "month": 12, "year": None, "period_key": "winter-unknown"}
    assert period_parse("some_milan_vlog", F)["season"] == "fall"
    assert period_parse("some_milan_vlog", "astream")["period_key"] == "unknown-unknown"
    ks = sorted([period_parse(x) for x in [V_JUNE, V26_02, V25_11, V25_02]], key=period_sort)
    assert [k["period_key"] for k in ks] == ["2025-02", "2025-11", "2026-02", "summer-unknown"]


def test3():
    """matrix counts, rates, evidence + contract keys"""
    m = matrix_build(fake_verdicts())
    assert set(m) == {"source", "items", "periods", "cells", "trend", "evidence"}
    assert m["periods"] == ["2025-02", "2025-11", "2026-02", "summer-unknown"]
    c = m["cells"]["suede jacket"]["2025-11"]
    assert c == {"pass": 2, "viewed": 4, "rate": 0.5}
    assert len(m["evidence"]["long wool coat"]["2025-11"]) == 3
    assert len(m["evidence"]["leopard print"]["2025-02"]) == 3
    assert "2026-02" not in m["evidence"]["leopard print"]


def test4():
    """trend labels"""
    m = matrix_build(fake_verdicts())
    assert m["trend"] == {"suede jacket": "rising", "long wool coat": "evergreen",
                          "leopard print": "fading", "ballet flats": "insufficient"}
    assert trend_label([0.5, 0.4, 0.45]) == "stable"
    assert trend_label([0.9, 0.9]) == "insufficient"


def test5():
    """dedup on (item, filename, ts_start_ms)"""
    rows = fake_verdicts()
    m = matrix_build(rows + rows[:3])
    assert m["cells"]["suede jacket"]["2025-02"]["viewed"] == 4


def test6():
    """CLI build writes json; md renders"""
    os.makedirs(dirtest, exist_ok=True)
    fin = os.path.join(dirtest, "verdicts.jsonl")
    with open(fin, "w") as f:
        f.write("\n".join(json.dumps(r) for r in fake_verdicts()))
    build(fin)
    with open(os.path.join(dirtest, "trend_matrix.json")) as f:
        m = json.load(f)
    assert m["trend"]["suede jacket"] == "rising"
    s = md_matrix(m)
    assert "| suede jacket | 1/4 | 2/4 | 4/4 | · | rising |" in s


def test7():
    """source filter: window rows excluded from street matrix, kept in window / all"""
    win = {"item": "suede jacket", "stream_name": F, "filename": V25_11, "ts_start_ms": 558000,
           "ts_end_ms": 561000, "verdict": "PASS", "evidence": "mannequin", "frame_png": "/tmp/w.png",
           "source": "window"}
    rows = fake_verdicts() + [win]
    assert matrix_build(rows)["cells"]["suede jacket"]["2025-11"]["viewed"] == 4
    mw = matrix_build(rows, "window")
    assert mw["items"] == ["suede jacket"]
    assert mw["cells"]["suede jacket"] == {"2025-11": {"pass": 1, "viewed": 1, "rate": 1.0}}
    assert mw["trend"]["suede jacket"] == "insufficient"
    assert matrix_build(rows, "all")["cells"]["suede jacket"]["2025-11"]["viewed"] == 5


def test_all():
    test1(); test2(); test3(); test4(); test5(); test6(); test7()
    print("test_trend_matrix: all ok")


if __name__ == "__main__":
    import fire
    fire.Fire()
