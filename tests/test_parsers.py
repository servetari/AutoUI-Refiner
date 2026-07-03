import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coder_agent import _extract_code, _looks_like_html
from utils import load_prompts
from vision_evaluator import _parse_evaluation


HTML_DOC = "<!DOCTYPE html>\n<html><body><h1>Hi</h1></body></html>"


class TestExtractCode:
    def test_plain_html_passes_through(self):
        assert _extract_code(HTML_DOC) == HTML_DOC

    def test_fenced_block_is_unwrapped(self):
        raw = f"```html\n{HTML_DOC}\n```"
        assert _extract_code(raw) == HTML_DOC

    def test_preamble_before_fence_is_dropped(self):
        raw = f"Sure! Here is the code:\n```html\n{HTML_DOC}\n```"
        assert _extract_code(raw) == HTML_DOC

    def test_preamble_before_doctype_is_dropped(self):
        raw = f"Here is your page:\n{HTML_DOC}"
        assert _extract_code(raw) == HTML_DOC

    def test_looks_like_html(self):
        assert _looks_like_html(HTML_DOC)
        assert not _looks_like_html("I'm sorry, I can't help with that.")


class TestLoadPrompts:
    def test_sections_are_split_on_line_start_headings(self, tmp_path):
        config = tmp_path / "config.md"
        config.write_text(
            "# First Prompt\nbody one\n\n# Second Prompt\nbody two\n",
            encoding="utf-8",
        )
        prompts = load_prompts(str(config))
        assert prompts == {"First Prompt": "body one", "Second Prompt": "body two"}

    def test_inline_hash_does_not_split_sections(self, tmp_path):
        config = tmp_path / "config.md"
        config.write_text(
            "# Only Prompt\nuse the # 1 heading style\n## sub heading stays\n",
            encoding="utf-8",
        )
        prompts = load_prompts(str(config))
        assert list(prompts) == ["Only Prompt"]
        assert "## sub heading stays" in prompts["Only Prompt"]

    def test_missing_file_returns_empty_dict(self):
        assert load_prompts("does_not_exist.md") == {}


class TestParseEvaluation:
    def test_valid_json(self):
        raw = '{"score": 7, "verdict": "FAIL", "issues": ["add gradient"]}'
        result = _parse_evaluation(raw)
        assert result["score"] == 7
        assert result["verdict"] == "FAIL"
        assert result["issues"] == ["add gradient"]

    def test_json_wrapped_in_fences_and_text(self):
        raw = 'Here you go:\n```json\n{"score": 9, "verdict": "PASS", "issues": []}\n```'
        result = _parse_evaluation(raw)
        assert result["score"] == 9
        assert result["verdict"] == "PASS"
        assert result["issues"] == []

    def test_garbage_falls_back_to_fail(self):
        result = _parse_evaluation("The design looks great, I would surpass it!")
        assert result["verdict"] == "FAIL"
        assert result["score"] == 0
        assert result["issues"]

    def test_score_is_clamped(self):
        raw = '{"score": 42, "verdict": "FAIL", "issues": ["x"]}'
        assert _parse_evaluation(raw)["score"] == 10
