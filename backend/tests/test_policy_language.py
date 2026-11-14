# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Language design / lexer, parser, interpreter tests
import ast
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.errors import PolicySyntaxError
from app.policy import (
    DefaultWritingMode,
    MayNotRead,
    MayNotSeeExistence,
    MayRead,
    MaySeeExistence,
    MentioningSelector,
    ProtocolBlock,
    TaggedSelector,
    TransferCustody,
    Trustee,
    interpret,
    lex,
    parse,
)

ROOT = Path(__file__).parents[2]
GRAMMAR_DIR = ROOT / "docs" / "grammar"


def test_handout_sample_policy_parses_verbatim_and_emits_expected_facts():
    source = (GRAMMAR_DIR / "sample_maria.policy").read_text(encoding="utf-8")

    facts = interpret(parse(source))

    assert facts == (
        "grant(maria, existence, mentioning(maria)).",
        "grant(maria, summary, tagged(family)).",
        "release(maria, 'To my daughter', date(2040,5,1)).",
        "custody_rule(adam_jr, trustee_unavailable, 90).",
        "default_mode(light_fix).",
    )


def test_protocol_ast_is_immutable_and_contains_typed_allow_and_deny_nodes():
    policy = parse(
        'protocol maria:\n'
        '    may see existence of entries mentioning lola\n'
        '    may read verbatim of entries tagged "Family"\n'
        '    may not see existence of entries mentioning adam\n'
        '    may not read summary of entries tagged "Private"\n'
    )
    block = policy.statements[0]

    assert isinstance(block, ProtocolBlock)
    assert isinstance(block.statements[0], MaySeeExistence)
    assert isinstance(block.statements[0].selector, MentioningSelector)
    assert isinstance(block.statements[1], MayRead)
    assert isinstance(block.statements[1].selector, TaggedSelector)
    assert isinstance(block.statements[2], MayNotSeeExistence)
    assert isinstance(block.statements[3], MayNotRead)
    with pytest.raises(FrozenInstanceError):
        block.person = "lola"
    with pytest.raises(TypeError, match="tuple"):
        ProtocolBlock("maria", [])


def test_deny_statements_compile_to_the_specified_deny_facts():
    source = (
        "protocol maria:\n"
        "    may not see existence of entries mentioning lola\n"
        '    may not read summary of entries tagged "Private"\n'
        '    may not read verbatim of entries tagged "Secrets"\n'
    )

    assert interpret(parse(source)) == (
        "deny(maria, existence, mentioning(lola)).",
        "deny(maria, summary, tagged(private)).",
        "deny(maria, verbatim, tagged(secrets)).",
    )


def test_uppercase_tag_is_casefolded_before_fact_emission():
    policy = parse(
        'protocol maria:\n'
        '    may read summary of entries tagged "FaMiLy"\n'
    )

    assert interpret(policy) == ("grant(maria, summary, tagged(family)).",)


def test_empty_protocol_block_is_valid_and_emits_no_facts():
    policy = parse("protocol maria:\n")

    assert policy.statements == (ProtocolBlock("maria", ()),)
    assert interpret(policy) == ()


def test_custody_rule_parses_without_a_trustee_statement():
    facts = interpret(
        parse("transfer custody to adam_jr if trustee unavailable for 90 days\n")
    )

    assert facts == ("custody_rule(adam_jr, trustee_unavailable, 90).",)


def test_optional_trustee_is_a_top_level_fact():
    policy = parse(
        "trustee is adam\n"
        "protocol maria:\n"
        "    may see existence of entries mentioning maria\n"
    )

    assert interpret(policy) == (
        "trustee(adam).",
        "grant(maria, existence, mentioning(maria)).",
    )
    assert isinstance(policy.statements[0], Trustee)


def test_duplicate_protocol_blocks_are_emitted_separately_and_in_source_order():
    policy = parse(
        "protocol maria:\n"
        "    may see existence of entries mentioning lola\n"
        "protocol maria:\n"
        '    may read summary of entries tagged "Family"\n'
    )

    assert interpret(policy) == (
        "grant(maria, existence, mentioning(lola)).",
        "grant(maria, summary, tagged(family)).",
    )
    assert len(policy.statements) == 2


def test_all_valid_sample_programs_parse_and_invalid_samples_raise():
    valid_paths = tuple(GRAMMAR_DIR.glob("sample_*.policy"))
    invalid_paths = tuple(GRAMMAR_DIR.glob("invalid_*.policy"))

    assert len(valid_paths) >= 3
    assert len(invalid_paths) >= 3
    for path in valid_paths:
        assert parse(path.read_text(encoding="utf-8")).statements
    for path in invalid_paths:
        with pytest.raises(PolicySyntaxError):
            parse(path.read_text(encoding="utf-8"))


def test_policy_statement_order_is_preserved_across_top_level_and_protocol_lines():
    policy = parse(
        "trustee is adam\n"
        "protocol maria:\n"
        "    may see existence of entries mentioning maria\n"
        "transfer custody to adam_jr if trustee unavailable for 4 days\n"
        "default writing mode: review\n"
    )

    assert interpret(policy) == (
        "trustee(adam).",
        "grant(maria, existence, mentioning(maria)).",
        "custody_rule(adam_jr, trustee_unavailable, 4).",
        "default_mode(review).",
    )
    assert isinstance(policy.statements[-1], DefaultWritingMode)
    assert isinstance(policy.statements[-2], TransferCustody)


def test_global_statements_are_rejected_inside_protocol_blocks():
    with pytest.raises(PolicySyntaxError, match="Expected 'may'"):
        parse(
            "protocol maria:\n"
            "    default writing mode: review\n"
        )


@pytest.mark.parametrize(
    ("source", "message", "line", "column"),
    [
        ("protocol maria\n", "Expected ':'", 1, 15),
        ("protocol maria:\n    may read summary of entries tagged \"Family\n",
         "Unterminated quoted string", 2, 40),
        ("protocol Maria:\n", "identifiers are lowercase", 1, 10),
        ("protocol may:\n", "reserved words cannot be identifiers", 1, 10),
        (
            "protocol maria:\n        may see existence of entries mentioning maria\n",
            "one indentation level",
            2,
            1,
        ),
    ],
)
def test_invalid_syntax_reports_readable_message_and_source_location(
    source, message, line, column
):
    with pytest.raises(PolicySyntaxError) as error:
        parse(source)

    assert message in str(error.value)
    assert error.value.line == line
    assert error.value.column == column


def test_invalid_calendar_date_reports_policy_syntax_error():
    with pytest.raises(PolicySyntaxError, match="valid calendar date"):
        parse("release letter \"Note\" to maria when date >= 2040-02-30\n")


def test_mixed_or_tab_indentation_is_rejected():
    with pytest.raises(PolicySyntaxError, match="four spaces"):
        lex("protocol maria:\n  may see existence of entries mentioning maria\n")
    with pytest.raises(PolicySyntaxError, match="Tabs are not allowed"):
        lex("protocol maria:\n\tmay see existence of entries mentioning maria\n")


def test_title_and_tag_atoms_are_escaped_without_raw_interpolation():
    title = "O'Brien \\ notes\nSecond line \u2603 \x01"
    tag = "Family'\\Tag\n\u2603"
    title_literal = json.dumps(title, ensure_ascii=False)
    tag_literal = json.dumps(tag, ensure_ascii=False)
    source = (
        f"release letter {title_literal} to maria when date >= 2040-05-01\n"
        "protocol maria:\n"
        f"    may read summary of entries tagged {tag_literal}\n"
    )

    facts = interpret(parse(source))

    assert facts == (
        r"release(maria, 'O\'Brien \\ notes\nSecond line ☃ \x1\', date(2040,5,1)).",
        r"grant(maria, summary, tagged('family\'\\tag\n☃')).",
    )
    assert "\x01" not in "\n".join(facts)


def test_policy_modules_do_not_import_flask_or_database_packages():
    source_dirs = (ROOT / "backend" / "app" / "policy", ROOT / "backend" / "app" / "errors")
    prohibited_imports = {"flask", "sqlalchemy", "pymysql"}

    for source_dir in source_dirs:
        for source_path in source_dir.glob("*.py"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".", 1)[0] for alias in node.names}
                    assert prohibited_imports.isdisjoint(roots)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert node.module.split(".", 1)[0] not in prohibited_imports
