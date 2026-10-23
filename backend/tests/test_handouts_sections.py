import pytest

from handouts.extract import extract_text
from handouts.sections import MAX_WORDS, chunk, sentences, split

PARA = "This paragraph explains how the practice works in ordinary sessions with a client present. " * 2


def headings(text):
    return [path for path, _ in split(text)[2]]


def test_title_and_date_come_from_the_top_of_the_document():
    title, date, _ = split(f"Garden Tools Review\n            (Mar 4, 2019)\n\nTools\n{PARA}")
    assert title == "Garden Tools Review"
    assert date == "Mar 4, 2019"


def test_short_unpunctuated_lines_and_marked_lines_are_headings():
    text = (f"Title\n\nOverview\n{PARA}\n"
            f"Part II: The Backstory\n{PARA}\n"
            f"Day 1: Prepare the Ground (~10 min)\n{PARA}\n"
            f"2) Plant the Seeds:\n{PARA}")
    assert headings(text) == [
        ("Overview",),
        ("Part II: The Backstory",),
        ("Part II: The Backstory", "Day 1: Prepare the Ground (~10 min)"),
        ("Part II: The Backstory", "2) Plant the Seeds"),
    ]


def test_a_long_numbered_paragraph_is_body_not_a_heading():
    text = f"Title\n\nDetails\n1. Roots & Soil. This is the first source and it is described at length here.\n{PARA}"
    assert headings(text) == [("Details",)]


def test_pdf_wrapped_lines_are_not_headings():
    text = ("Title\n\nWhat is a garden?\n"
            "A garden is a place where plants grow and\n"
            "people tend them over many seasons of\n"
            "patient work, and the soil improves.\n" + PARA)
    _, _, sections = split(text)
    assert [p for p, _ in sections] == [("What is a garden?",)]
    assert "grow and people tend them" in sections[0][1]


def test_page_debris_toc_lines_and_date_lines_are_dropped():
    text = f"Title\n\nJan 1, 2013\nSoil\n{PARA}\nPAGE  2\n{PARA}\nContents ………………… 12\n{PARA}\n(Feb 26, 2022)\n{PARA}\nPAGE  \n"
    _, _, sections = split(text)
    assert [p for p, _ in sections] == [("Soil",)]
    assert "PAGE" not in sections[0][1] and "Contents" not in sections[0][1]


def test_a_tiny_section_is_folded_into_the_next_one():
    text = f"Title\n\nTiny Part\nJust a few words.\nReal Part\n{PARA}"
    _, _, sections = split(text)
    assert [p for p, _ in sections] == [("Real Part",)]
    assert sections[0][1].startswith("Tiny Part Just a few words.")


@pytest.mark.parametrize("text, count", [
    ("Use approx. 5 drops. Then rest.", 2),
    ("Bring tools, e.g. Shears and gloves. Then start.", 2),
    ("It takes ~10 min. Then stop.", 2),
    ("1. First step here. 2. Second step here.", 2),
    ("Is it ready? Yes! Begin now.", 3),
])
def test_sentence_breaks_skip_abbreviations_and_list_markers(text, count):
    assert len(sentences(text)) == count


def test_chunks_stay_within_size_and_overlap_by_one_sentence():
    text = " ".join(f"Sentence number {i} talks about the garden in some detail for a while." for i in range(120))
    chunks = chunk(text)
    assert len(chunks) > 1
    assert all(len(c.split()) <= MAX_WORDS for c in chunks)
    for a, b in zip(chunks, chunks[1:]):
        assert sentences(a)[-1] == sentences(b)[0]


def test_a_sentence_longer_than_a_chunk_is_cut_into_windows():
    chunks = chunk(" ".join(["word"] * (MAX_WORDS * 2 + 10)))
    assert all(len(c.split()) <= MAX_WORDS for c in chunks)
    assert sum(len(c.split()) for c in chunks) >= MAX_WORDS * 2 + 10


def test_chunks_never_cross_sections():
    text = f"Title\n\nRoses\n{'Roses need sun every day. ' * 200}\nFerns\n{'Ferns like shade most days. ' * 200}"
    for path, body in split(text)[2]:
        for c in chunk(body):
            assert ("Roses" in c) != ("Ferns" in c)


def test_extract_rejects_unknown_types(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("x")
    with pytest.raises(ValueError):
        extract_text(f)
