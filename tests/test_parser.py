"""Tests for sectioned text parsing utilities."""

from wnt.utils.utils_parser import SectionedText, format_tokens, parse_tokens


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


def test_sectioned_text_normalizes_section_names(tmp_path):
    source = tmp_path / "mixed_case.inp"
    source.write_text("[ Junctions ]\nJ1 10\n[end]\n", encoding="latin-1")

    sectioned = SectionedText()
    sectioned.read(source)

    assert sectioned.sections == {"JUNCTIONS": ["J1 10"]}
