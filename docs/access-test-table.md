<!-- Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator) -->
# ENNOVA Prolog Access Test Table

The test suite reads this table and sends each row to SWI-Prolog. The
`maria_acceptance` rows are batched together after parsing and interpreting the
handout sample policy. All active contexts include entries for `e_maria`
(diary, mentioned name `Maria`), `e_family` (diary, tag `Family`), `e_business`
(diary, tag `Business`), `e_private` (diary, tag `Private`), `e_secret` (diary,
mentioned name `Secret`), `e_archive` (diary, tag `Archive`), and `e_letter`
(letter titled `To my daughter`, tag `Letters`). Active registration includes
`maria` and `nora`; death is triggered. Context variants only alter the noted
fact. App-side names and tags are case-folded before they become Prolog facts.
The broader backend verification approach is documented in
[`test-plan.md`](test-plan.md). The demo, grounded-Q&A, and entry-store tests
share fictional diary data from `backend/scripts/maria_fixture.py`; this table
keeps compact synthetic facts for isolated Prolog rule cases.

| Scenario | Asker | Entry ID | Level | Today | Policy | Context | Expected |
|---|---|---|---|---|---|---|---|
| maria_acceptance | maria | e_maria | existence | 2040-05-01 | maria_sample | active | allow |
| maria_acceptance | maria | e_family | summary | 2040-05-01 | maria_sample | active | allow |
| maria_acceptance | maria | e_letter | verbatim | 2040-04-30 | maria_sample | active | deny |
| maria_acceptance | maria | e_letter | verbatim | 2040-05-01 | maria_sample | active | allow |
| maria_acceptance | maria | e_business | summary | 2040-05-01 | maria_sample | active | deny |
| maria_acceptance | nora | e_family | summary | 2040-05-01 | maria_sample | active | deny |
| hierarchy | maria | e_archive | existence | 2040-05-01 | archive_verbatim | active | allow |
| hierarchy | maria | e_archive | summary | 2040-05-01 | archive_verbatim | active | allow |
| hierarchy | maria | e_archive | verbatim | 2040-05-01 | archive_verbatim | active | allow |
| hierarchy | maria | e_family | verbatim | 2040-05-01 | maria_sample | active | deny |
| deny_override | maria | e_private | summary | 2040-05-01 | private_deny | active | deny |
| deny_override | maria | e_private | verbatim | 2040-05-01 | private_deny | active | deny |
| deny_override | maria | e_secret | existence | 2040-05-01 | private_deny | active | deny |
| deny_override | maria | e_secret | summary | 2040-05-01 | private_deny | active | deny |
| deny_override | maria | e_secret | verbatim | 2040-05-01 | private_deny | active | deny |
| registration | guest | e_family | verbatim | 2040-05-01 | guest_grant | active | deny |
| death_trigger | maria | e_family | summary | 2040-05-01 | maria_sample | before_death | deny |
| release_hierarchy | maria | e_letter | existence | 2040-05-01 | maria_sample | active | allow |
| release_hierarchy | maria | e_letter | summary | 2040-05-01 | maria_sample | active | allow |
| release_hierarchy | maria | e_letter | verbatim | 2040-05-01 | maria_sample | active | allow |
| release_hierarchy | maria | e_letter | summary | 2040-04-30 | maria_sample | active | deny |
| broad_grant_letter | maria | e_letter | verbatim | 2040-05-01 | letters_grant | active | deny |
| wrong_recipient | nora | e_letter | verbatim | 2040-05-01 | maria_sample | active | deny |
| deny_release | maria | e_letter | verbatim | 2040-05-01 | letter_deny | active | deny |
| default_deny | maria | missing_entry | summary | 2040-05-01 | maria_sample | active | deny |

`Policy` keys are test policy sources: `maria_sample` is
[`sample_maria.policy`](grammar/sample_maria.policy); `archive_verbatim`,
`private_deny`, `guest_grant`, `letters_grant`, and `letter_deny` are small
policies defined by the table-driven test. The tests group rows by policy and
context and send each group as one batch.

## Bridge choice

The Python bridge uses a one-shot `swipl` subprocess instead of PySwip. This
avoids a native Python binding/shared-library version dependency and gives each
evaluation process isolation plus a strict timeout. Process startup is slower
than a persistent PySwip runtime, but is a simpler initial integration for the
required SWI-Prolog installation. The bridge invokes a fixed executable argument
list (`-f none`, quiet mode, the trusted rules file, and a fixed runner goal)
with no shell. Input is read with Prolog `read_term/3` as data, each term is
whitelisted before assertion, and input is never consulted as source.
