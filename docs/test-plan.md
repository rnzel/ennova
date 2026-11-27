# ENNOVA Backend Test Plan

## Purpose and scope

This plan describes verification of the ENNOVA diary model, entry processing, integrity chain, writing modes, Legacy Policy language and Prolog authorization, and grounded AI question answering. It maps expected outcomes to automated tests; it is not a test execution report. Record actual command output separately when running the plan.

## Test environment and prerequisites

- Use the Python environment and dependency setup in the repository root `README.md`; install backend packages with `pip install -r backend/requirements.txt`.
- Run commands from `backend/` unless a command says otherwise.
- Install SWI-Prolog and make `swipl` available on `PATH`, or configure `SWIPL_EXECUTABLE`. Required Prolog integration tests fail if it is absent.
- Default tests use deterministic fake model clients and do not require a live AI provider. Live AI checks are opt-in with `RUN_LIVE_AI_TESTS=1` and the provider configuration described in `backend/.env.example`.
- MySQL persistence checks require configured database credentials. A skip or prerequisite failure is not a passing integration check.
- Use only the fictional records described below. Do not enter real diary or beneficiary data.

## Test data

`backend/scripts/maria_fixture.py` is the shared deterministic fixture consumed by the Maria demo and backend acceptance tests. It defines Lola, 20 fictional diary records dated from 2017 through 2026, Maria and Nora as registered people, and one separate fictional letter to Maria. The diary records include multiple family-tagged entries, several business-tagged entries, and two explicit Maria mentions for existence-level access. The fixture reads the release date for `To my daughter` from `docs/grammar/sample_maria.policy` and stores that date as letter metadata; policy remains the authorization source.

`docs/access-test-table.md` contains the table-driven Prolog matrix, including the six handout acceptance scenarios and additional allow, deny, hierarchy, registration, lifecycle, recipient, and default-deny cases. Some bridge tests use deliberately small synthetic facts to isolate rule behavior.

## Test strategy and execution

Use deterministic unit tests for pure transformations and domain behavior, table-driven SWI-Prolog integration tests for policy decisions, and service/API tests with scripted fake model responses for authorization and data-flow boundaries. Run focused tests while changing an area, then the full backend suite. Preserve command output and exit codes; only report a test as passed when its command completed successfully.

From `backend/`, the focused commands are:

```powershell
pytest -q tests/test_entry_store.py
pytest -q tests/test_prolog_access.py
pytest -q tests/test_grounded_qa.py
pytest -q tests/test_demo_maria.py
pytest -q tests/test_writing_modes.py
pytest -q tests/test_processing.py
pytest -q tests/test_policy_language.py
```

Then run the full suite:

```powershell
pytest
```

## Test cases and expected outcomes

| Component | Existing tests and paths | Expected outcome |
|---|---|---|
| A. Diary model (OOP) | `backend/tests/test_diary_model.py`: `test_entry_hierarchy_and_polymorphic_kind`, `test_entry_content_and_metadata_are_read_only`, `test_vault_appends_retrieves_and_returns_immutable_snapshots`, `test_vault_rejects_duplicate_ids_and_has_no_edit_or_delete_methods`, `test_owner_beneficiary_and_protocol_keep_encapsulated_identity_and_grants`, `test_beneficiary_protocol_is_optional_and_type_checked` | Diary and letter types retain identity and original content; vault snapshots are immutable; duplicate IDs and invalid model relationships are rejected. |
| B. Functional entry processing and immutable data | `backend/tests/test_processing.py`: `test_normalize_canonicalizes_unicode_and_newlines_only`, `test_extract_names_reads_links_and_known_aliases_in_order`, `test_extract_topics_casefolds_and_deduplicates_in_first_seen_order`, `test_correct_applies_immutable_rules_in_order_and_preserves_simple_case`, `test_diff_segments_reconstruct_both_original_and_updated_text`, `test_entry_data_is_frozen_and_metadata_is_immutable`; `backend/tests/test_entry_store.py`: `test_service_keeps_original_text_and_binds_hash_to_owner_entry_and_timestamp`, `test_sample_documents_expected_mentions_tags_and_policy_recipient` | Transformations are deterministic, immutable inputs stay immutable, extracted metadata is correct, and saved entries retain the original text and timestamp. The shared fixture contains 20 diary entries and one separate letter. |
| C. Hash-chain integrity and tamper detection | `backend/tests/test_processing.py`: `test_hash_chain_is_deterministic_and_links_each_entry_to_its_predecessor`, `test_hash_chain_detects_content_timestamp_and_metadata_tampering`, `test_hash_chain_detects_digest_and_predecessor_link_tampering`; `backend/tests/test_entry_store.py`: `test_letter_release_metadata_is_bound_to_the_entry_hash`, `test_verify_checks_expected_head_and_detects_chain_tampering` | Valid chains verify; changes to entry content, timestamp, metadata, release-date metadata, digests, links, or expected head are detected. |
| D. Writing modes | `backend/tests/test_writing_modes.py`: `test_verbatim_preserves_original_and_has_no_diff`, `test_light_fix_reuses_f2_rules_without_changing_source`, `test_review_reports_exact_suggestion_records`, `test_review_optional_rewrite_and_no_matching_rule_is_unchanged`, `test_registry_dispatches_without_mode_conditionals`, `test_unknown_mode_error_and_safe_resolver_fallback`, `test_policy_without_default_resolves_verbatim_without_raising` | Verbatim preserves source text, Light Fix creates a derived corrected view without changing source, and Review reports suggestions or applies an explicit rewrite. Invalid or absent mode configuration uses the safe fallback. |
| E. Prolog access rules and Legacy Policy language | `backend/tests/test_policy_language.py`: `test_handout_sample_policy_parses_verbatim_and_emits_expected_facts`, `test_deny_statements_compile_to_the_specified_deny_facts`, `test_all_valid_sample_programs_parse_and_invalid_samples_raise`, `test_invalid_syntax_reports_readable_message_and_source_location`, `test_invalid_calendar_date_reports_policy_syntax_error`; `backend/tests/test_prolog_access.py`: `test_maria_scenario_parses_interprets_loads_and_queries_in_one_batch`, `test_access_rules_are_driven_by_the_documented_table`, `test_query_values_are_escaped_as_data_not_interpreted_as_prolog`, `test_untrusted_directive_is_read_as_data_and_denied`, `test_unlisted_input_predicate_is_whitelisted_out_and_denied` | Lexer/parser errors are located and safe; interpretation emits expected facts; Prolog evaluates the access table, denies by default, preserves deny-overrides, and rejects unsafe or unlisted input. |
| F. Grounded AI Q&A | `backend/tests/test_grounded_qa.py`: `test_six_maria_scenarios_end_to_end_with_scripted_model`, `test_letter_status_released_iff_verbatim_access_is_allowed`, `test_denied_and_nonexistent_entry_responses_are_byte_identical`, `test_no_permitted_entry_means_no_model_call`, `test_citations_drop_unpresented_ids_and_use_stored_dates`, `test_only_permitted_entries_are_integrity_checked`, `test_tampered_entry_is_excluded_while_other_permitted_entry_remains`; `backend/tests/test_owner_qa.py`: `test_owner_endpoint_is_authenticated_owner_scoped_and_keeps_ask_separate`, `test_owner_endpoint_rejects_missing_invalid_and_beneficiary_authentication`, `test_owner_no_record_and_invalid_citation_are_safe` | Beneficiary retrieval is Prolog-authorized before content is returned; owner retrieval remains authenticated and owner-scoped; citations only name presented entries and use stored dates; denied or unsupported requests do not expose evidence to the model. The Maria test checks the complete original letter and citation on its release date. |

## Required Maria acceptance cases

These are exercised at the grounded-Q&A layer in `test_six_maria_scenarios_end_to_end_with_scripted_model` and at the Prolog decision layer by the six `maria_acceptance` rows in `docs/access-test-table.md`:

1. **Existence:** report the count of permitted Maria mentions without diary text or citations.
2. **Family summary:** answer from permitted family summaries and attach entry IDs and stored dates.
3. **Before release:** on 2040-04-30, refuse the letter request with its release date; do not send its contents to the model.
4. **At release:** on 2040-05-01, provide the complete original letter text and cite `e_letter` with its stored entry date.
5. **Business without permission:** return the shared neutral response without confirming or denying a matching business entry; restricted text must not appear in model input.
6. **No protocol:** Nora's request returns the same neutral response without exposing content or calling the model.

## Security and failure-case testing

- `backend/tests/test_errors.py` checks typed exceptions, private internal details, and safe public fallbacks, including `test_access_denied_reasons_have_byte_identical_public_messages` and `test_public_response_uses_only_typed_public_fields`.
- `backend/tests/test_api_security.py` checks neutral denied/no-record API responses, unredeemed beneficiaries, private audit records, request limits, and sensitive exception canaries.
- `backend/tests/test_grounded_qa.py` checks denied content is excluded from model prompts, citations are filtered, tampered records are excluded, unauthorized letter titles do not reach the model, and Prolog/model failures fail closed.
- `backend/tests/test_owner_qa.py` verifies authentication, owner isolation, rejection of beneficiary credentials on the owner route, and safe no-record and invalid-citation behavior.
- `backend/tests/test_demo_maria.py` checks scripted demo responses, the release-date boundary, exact post-release letter text, neutral business/Nora responses, restricted canary exclusion, and safe provider failure output.

## Result recording

This plan defines cases and expected outcomes only. A run report must list the actual commands, pass/fail/skip counts, and prerequisite failures. No test result is implied by the presence of a test or by this document.
