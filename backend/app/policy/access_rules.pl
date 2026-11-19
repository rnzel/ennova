% Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)

:- dynamic registered/1.
:- dynamic death_triggered/0.
:- dynamic policy_frozen/0.
:- dynamic entry/2.
:- dynamic entry_mentions/2.
:- dynamic entry_tag/2.
:- dynamic letter/2.
:- dynamic grant/3.
:- dynamic deny/3.
:- dynamic release/3.
:- dynamic trustee/1.
:- dynamic custody_rule/3.
:- dynamic default_mode/1.

level_rank(existence, 1).
level_rank(summary, 2).
level_rank(verbatim, 3).

can_access(Person, EntryId, Level, Today, Decision) :-
    (   \+ registered(Person)
    ->  Decision = deny
    ;   \+ death_triggered
    ->  Decision = deny
    ;   \+ valid_access_request(EntryId, Level, Today)
    ->  Decision = deny
    ;   explicit_deny(Person, EntryId, Level)
    ->  Decision = deny
    ;   permitted_entry(Person, EntryId, Level, Today)
    ->  Decision = allow
    ;   Decision = deny
    ).

letter_status(Person, Title, Today, Status) :-
    (   valid_date(Today),
        letter(EntryId, Title),
        can_access(Person, EntryId, verbatim, Today, allow)
    ->  Status = released
    ;   eligible_future_release(Person, Title, Today)
    ->  Status = not_yet
    ;   Status = none
    ).

eligible_future_release(Person, Title, Today) :-
    registered(Person),
    death_triggered,
    letter(EntryId, Title),
    unique_letter_title(EntryId, Title),
    entry(EntryId, letter),
    release(Person, Title, ReleaseDate),
    valid_date(Today),
    valid_date(ReleaseDate),
    \+ explicit_deny(Person, EntryId, verbatim),
    date_key(Today, TodayKey),
    date_key(ReleaseDate, ReleaseKey),
    TodayKey < ReleaseKey.

valid_access_request(EntryId, Level, Today) :-
    memberchk(Level, [existence, summary, verbatim]),
    valid_date(Today),
    entry(EntryId, Type),
    memberchk(Type, [diary, letter]),
    \+ (entry(EntryId, OtherType), OtherType \= Type).

explicit_deny(Person, EntryId, RequestedLevel) :-
    deny(Person, DenyLevel, Selector),
    selector_matches(Selector, EntryId),
    level_rank(DenyLevel, DenyRank),
    level_rank(RequestedLevel, RequestRank),
    RequestRank >= DenyRank.

permitted_entry(Person, EntryId, RequestedLevel, _Today) :-
    entry(EntryId, diary),
    \+ entry(EntryId, letter),
    \+ letter(EntryId, _),
    grant(Person, GrantLevel, Selector),
    selector_matches(Selector, EntryId),
    level_rank(GrantLevel, GrantRank),
    level_rank(RequestedLevel, RequestRank),
    RequestRank =< GrantRank.
permitted_entry(Person, EntryId, _RequestedLevel, Today) :-
    entry(EntryId, letter),
    letter(EntryId, Title),
    unique_letter_title(EntryId, Title),
    release(Person, Title, ReleaseDate),
    valid_date(ReleaseDate),
    date_key(Today, TodayKey),
    date_key(ReleaseDate, ReleaseKey),
    TodayKey >= ReleaseKey.

unique_letter_title(EntryId, Title) :-
    % A title-keyed release must not authorize ambiguous letter facts.
    letter(EntryId, Title),
    \+ (letter(OtherEntryId, Title), OtherEntryId \= EntryId).

selector_matches(mentioning(Name), EntryId) :-
    entry_mentions(EntryId, Name).
selector_matches(tagged(Tag), EntryId) :-
    entry_tag(EntryId, Tag).

can_modify_policy(_Person) :-
    \+ policy_frozen.

valid_date(date(Year, Month, Day)) :-
    integer(Year),
    Year >= 1,
    integer(Month),
    between(1, 12, Month),
    days_in_month(Year, Month, LastDay),
    integer(Day),
    between(1, LastDay, Day).

days_in_month(Year, 2, 29) :-
    leap_year(Year),
    !.
days_in_month(_, 2, 28).
days_in_month(_, Month, 30) :-
    memberchk(Month, [4, 6, 9, 11]),
    !.
days_in_month(_, Month, 31) :-
    memberchk(Month, [1, 3, 5, 7, 8, 10, 12]).

leap_year(Year) :-
    0 is Year mod 400,
    !.
leap_year(Year) :-
    0 is Year mod 4,
    Year mod 100 =\= 0.

date_key(date(Year, Month, Day), Key) :-
    Key is Year * 10000 + Month * 100 + Day.

run_from_stdin :-
    set_stream(user_input, encoding(utf8)),
    catch(read_input_terms(Terms), _, fail),
    !,
    process_input_terms(Terms).
run_from_stdin :-
    write(deny).

read_input_terms(Terms) :-
    read_term(user_input, Term, [syntax_errors(error)]),
    (   Term == end_of_file
    ->  Terms = []
    ;   Terms = [Term|Rest],
        read_input_terms(Rest)
    ).

process_input_terms(Terms) :-
    append(ContextFacts, [request_batch(Requests)], Terms),
    is_list(Requests),
    !,
    (   maplist(valid_context_fact, ContextFacts)
    ->  maplist(assertz, ContextFacts),
        maplist(evaluate_request, Requests, Decisions)
    ;   maplist(deny_request, Requests, Decisions)
    ),
    write_decisions(Decisions).
process_input_terms(_) :-
    write(deny).

valid_context_fact(Fact) :-
    ground(Fact),
    allowed_context_fact(Fact).

allowed_context_fact(registered(Person)) :-
    atom(Person).
allowed_context_fact(death_triggered).
allowed_context_fact(policy_frozen).
allowed_context_fact(entry(EntryId, Type)) :-
    atom(EntryId),
    memberchk(Type, [diary, letter]).
allowed_context_fact(entry_mentions(EntryId, Name)) :-
    atom(EntryId),
    atom(Name).
allowed_context_fact(entry_tag(EntryId, Tag)) :-
    atom(EntryId),
    atom(Tag).
allowed_context_fact(letter(EntryId, Title)) :-
    atom(EntryId),
    atom(Title).
allowed_context_fact(grant(Person, Level, Selector)) :-
    atom(Person),
    memberchk(Level, [existence, summary, verbatim]),
    valid_selector(Selector).
allowed_context_fact(deny(Person, Level, Selector)) :-
    atom(Person),
    memberchk(Level, [existence, summary, verbatim]),
    valid_selector(Selector).
allowed_context_fact(release(Person, Title, Date)) :-
    atom(Person),
    atom(Title),
    valid_date(Date).
allowed_context_fact(trustee(Person)) :-
    atom(Person).
allowed_context_fact(custody_rule(Person, trustee_unavailable, Days)) :-
    atom(Person),
    integer(Days),
    Days >= 0.
allowed_context_fact(default_mode(Mode)) :-
    memberchk(Mode, [verbatim, light_fix, review]).

valid_selector(mentioning(Name)) :-
    atom(Name).
valid_selector(tagged(Tag)) :-
    atom(Tag).

evaluate_request(access_request(Person, EntryId, Level, Today), Decision) :-
    !,
    (   ground(access_request(Person, EntryId, Level, Today)),
        atom(Person),
        atom(EntryId),
        memberchk(Level, [existence, summary, verbatim]),
        valid_date(Today)
    ->  (   catch(can_access(Person, EntryId, Level, Today, Result), _, fail)
        ->  Decision = Result
        ;   Decision = deny
        )
    ;   Decision = deny
    ).
evaluate_request(policy_request(Person), Decision) :-
    !,
    (   ground(Person),
        atom(Person),
        catch(can_modify_policy(Person), _, fail)
    ->  Decision = allow
    ;   Decision = deny
    ).
evaluate_request(letter_status_request(Person, Title, Today), Status) :-
    !,
    (   ground(letter_status_request(Person, Title, Today)),
        atom(Person),
        atom(Title),
        valid_date(Today)
    ->  (   catch(letter_status(Person, Title, Today, Result), _, fail)
        ->  Status = Result
        ;   Status = none
        )
    ;   Status = none
    ).
evaluate_request(_, deny).

deny_request(_, deny).

write_decisions([]).
write_decisions([Decision|Rest]) :-
    write(Decision),
    nl,
    write_decisions(Rest).
