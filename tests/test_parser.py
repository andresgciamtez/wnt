"""Tests for sectioned text parsing utilities."""

from wnt.utils.parser import SectionedText, format_tokens, parse_tokens


def test_parse_and_format_tokens():
    """Token helpers convert between text lines and token sequences."""
    tokens = parse_tokens("  J1   10.5   pattern  ")

    assert tokens == ("J1", "10.5", "pattern")
    assert format_tokens(tokens) == "J1    10.5    pattern"


def test_sectioned_text_round_trip(tmp_path):
    """SectionedText reads comments, sections, and data lines predictably."""
    source = tmp_path / "source.inp"
    target = tmp_path / "target.inp"
    source.write_text(
        "\n".join(
            [
                "[TITLE]",
                "; ignored comment",
                "Example model",
                "[JUNCTIONS]",
                "J1 10 ; inline comment",
                "[END]",
            ]
        ),
        encoding="latin-1",
    )

    sectioned = SectionedText()
    sectioned.read(source)
    sectioned.write(target)

    assert sectioned.sections == {
        "TITLE": ["Example model"],
        "JUNCTIONS": ["J1 10"],
    }
    assert "[END]" in target.read_text(encoding="latin-1")
