"""Ca bổ sung Bước 2, chỉ tạo dữ liệu giả trong tmp_path.

Chạy: python -m pytest scripts/test_step2_edges.py -q
"""
from PIL import Image
from pipeline.common import Dataset, load_config
from pipeline.checks import label_format, second_opinion
from pipeline.steps import autofix


def dataset(tmp_path, text):
    (tmp_path / "images").mkdir()
    (tmp_path / "labels").mkdir()
    Image.new("RGB", (640, 480)).save(tmp_path / "images" / "sample.JPG")
    (tmp_path / "labels" / "sample.txt").write_text(text, encoding="utf-8")
    cfg = load_config()
    return Dataset(tmp_path, cfg["classes"]), cfg


def test_two_errors_drop_wins_and_second_pass_is_empty(tmp_path):
    ds, cfg = dataset(tmp_path, "1 .95 .5 .2 .2\n1 .95 .5 .2 .2\n")
    issues = label_format.run(ds, cfg)
    assert {i.code for i in issues if i.line == 2} == {"BOX_OUT_OF_IMAGE", "DUP_BOX"}
    fixes = autofix.fix(ds, issues, cfg)
    assert [(f["line"], f["action"]) for f in fixes] == [(1, "clip_box"), (2, "drop_line")]
    assert autofix.fix(ds, label_format.run(ds, cfg), cfg) == []


def test_blank_lines_keep_numbers_across_checks_and_fix(tmp_path):
    ds, cfg = dataset(tmp_path, "0 .5 .5 .2 .2\n\n93 .3 .3 .2 .2\n\n1 .1 .1 .1 .1\n")
    issues = label_format.run(ds, cfg)
    assert [(i.code, i.line) for i in issues] == [("BAD_CLASS_ID", 3)]
    preds = {"sample": [[0, .9, .5, .5, .2, .2]]}
    assert [(i.code, i.line) for i in second_opinion.run(ds, cfg, preds)] == [("POSSIBLE_FALSE_POS", 5)]
    assert autofix.fix(ds, issues, cfg)[0]["line"] == 3
    assert ds.label_path("sample").read_text().splitlines() == ["0 .5 .5 .2 .2", "", "", "1 .1 .1 .1 .1"]


def test_multiple_predictions_keep_order_and_only_warn(tmp_path):
    ds, cfg = dataset(tmp_path, "0 .5 .5 .2 .2\n1 .1 .8 .1 .1\n")
    preds = {"sample": [[2, .91, .5, .5, .2, .2], [1, .92, .1, .1, .1, .2], [3, .93, .8, .8, .2, .2]]}
    issues = second_opinion.run(ds, cfg, preds)
    assert [(i.code, i.line) for i in issues] == [("POSSIBLE_WRONG_CLASS", None), ("POSSIBLE_MISSING", None), ("POSSIBLE_MISSING", None), ("POSSIBLE_FALSE_POS", 2)]
    assert all(i.severity == "warn" for i in issues)
    assert [i.extra["conf"] for i in issues[:3]] == [.91, .92, .93]


def test_infinite_class_id_does_not_crash(tmp_path):
    ds, cfg = dataset(tmp_path, "inf .5 .5 .2 .2\n")
    assert label_format.run(ds, cfg)[0].code == "BAD_FORMAT"
    assert second_opinion.run(ds, cfg, {"sample": []}) == []
