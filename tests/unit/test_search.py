"""Tests for the search utilities module."""

import pytest

from wmx.search import extract_searchable_text, keyword_match, search_items


class TestKeywordMatch:
    def test_single_keyword_match(self):
        assert keyword_match("hello", "hello world")
        assert keyword_match("world", "hello world")

    def test_single_keyword_no_match(self):
        assert not keyword_match("goodbye", "hello world")

    def test_multiple_keywords_all_present(self):
        assert keyword_match("hello world", "hello beautiful world")
        assert keyword_match("a b c", "a b c d e")

    def test_multiple_keywords_partial_match(self):
        # AND logic - all keywords must match
        assert not keyword_match("hello goodbye", "hello world")
        assert not keyword_match("a b z", "a b c d e")

    def test_case_insensitive_default(self):
        assert keyword_match("HELLO", "hello world")
        assert keyword_match("hello", "HELLO WORLD")
        assert keyword_match("HeLLo WoRLd", "hello world")

    def test_case_sensitive(self):
        assert not keyword_match("HELLO", "hello world", case_sensitive=True)
        assert keyword_match("hello", "hello world", case_sensitive=True)

    def test_empty_query(self):
        assert not keyword_match("", "hello world")

    def test_empty_text(self):
        assert not keyword_match("hello", "")

    def test_both_empty(self):
        assert not keyword_match("", "")


class TestExtractSearchableText:
    def test_string_field(self):
        item = {"path": "f/team/script"}
        text = extract_searchable_text(item, ["path"])
        assert text == "f/team/script"

    def test_multiple_string_fields(self):
        item = {"path": "f/team/script", "description": "A test script"}
        text = extract_searchable_text(item, ["path", "description"])
        assert "f/team/script" in text
        assert "A test script" in text

    def test_missing_field(self):
        item = {"path": "f/team/script"}
        text = extract_searchable_text(item, ["path", "nonexistent"])
        assert text == "f/team/script"

    def test_dict_field_serialized(self):
        item = {"path": "f/test", "value": {"nested": "content", "num": 42}}
        text = extract_searchable_text(item, ["path", "value"])
        assert "f/test" in text
        assert "nested" in text
        assert "content" in text
        assert "42" in text

    def test_list_field_serialized(self):
        item = {"path": "f/test", "tags": ["tag1", "tag2"]}
        text = extract_searchable_text(item, ["path", "tags"])
        assert "f/test" in text
        assert "tag1" in text
        assert "tag2" in text

    def test_numeric_field(self):
        item = {"path": "f/test", "version": 123}
        text = extract_searchable_text(item, ["path", "version"])
        assert "f/test" in text
        assert "123" in text


class TestSearchItems:
    def test_basic_search(self):
        items = [
            {"path": "f/team/script1"},
            {"path": "f/team/script2"},
            {"path": "f/other/script3"},
        ]
        results = search_items(items, "team", ["path"])
        assert len(results) == 2
        assert results[0]["path"] == "f/team/script1"
        assert results[1]["path"] == "f/team/script2"

    def test_search_with_limit(self):
        items = [{"path": f"f/match{i}"} for i in range(10)]
        results = search_items(items, "match", ["path"], limit=3)
        assert len(results) == 3

    def test_search_multiple_fields(self):
        items = [
            {"path": "f/test", "content": "def main(): pass"},
            {"path": "f/other", "content": "def helper(): return 42"},
        ]
        results = search_items(items, "main", ["path", "content"])
        assert len(results) == 1
        assert results[0]["path"] == "f/test"

    def test_search_no_matches(self):
        items = [
            {"path": "f/team/script1"},
            {"path": "f/team/script2"},
        ]
        results = search_items(items, "nonexistent", ["path"])
        assert len(results) == 0

    def test_search_empty_items(self):
        results = search_items([], "query", ["path"])
        assert len(results) == 0

    def test_search_case_sensitive(self):
        items = [
            {"path": "f/Team/Script"},
            {"path": "f/team/script"},
        ]
        results = search_items(items, "Team", ["path"], case_sensitive=True)
        assert len(results) == 1
        assert results[0]["path"] == "f/Team/Script"

    def test_search_nested_json(self):
        items = [
            {"path": "f/flow1", "value": {"modules": [{"script_path": "f/team/helper"}]}},
            {"path": "f/flow2", "value": {"modules": [{"script_path": "f/other/util"}]}},
        ]
        results = search_items(items, "helper", ["path", "value"])
        assert len(results) == 1
        assert results[0]["path"] == "f/flow1"
