# RegulonDB License Compliance

Terms read on 2026-11-06 at
<https://regulondb.ccg.unam.mx/manual/aboutUs/terms-conditions> (EULA version 2.0,
April 2006). This note is an engineering reading, not legal advice.

## What the terms say

The earlier project note that the license "forbids redistribution, so raw responses
stay ignored" was too narrow. The agreement covers more than raw files:

- Use is limited to academic, noncommercial end users, for internal purposes.
- Third parties may not get access to the database or to partial copies without
  UNAM's explicit consent, unless they hold their own valid agreement (clause 2.3).
- The user may not distribute the database, install it on a server or network, or
  let third parties access it (3.1).
- The user may not modify it or create derivative works (3.2).
- The user may not disclose, or let others reach, any data contained in it (3.5).
- Expanding it or integrating it into another databank needs prior written consent
  from CCG-UNAM.
- Copyright notices stay unchanged in copies (2.2).
- The term is one year from receipt, and partial contents must be deleted on leaving
  the current academic address.
- Works that use it cite the publication named in the terms.

## How this repository handles it

| Content | Treatment |
| --- | --- |
| Raw responses and the TSS union | Local, under the ignored data root |
| Placement ledgers and pair ledgers with support classes | Local, ignored |
| Row-level facts: TSS support class or distance per record, resolved locus, offsets | Local, ignored; tracked files hold redacted copies |
| Dataset identifiers, file hashes, query text, code | Tracked; these describe the acquisition and hold no database records |
| Aggregate counts, such as union size and class totals | Tracked; review them before any publication |
| ECK identifiers, promoter names, and coordinates in CNNProm headers | Tracked as CNNProm source data, which is not this acquisition |

Files kept local: the pilot contracts v1 and v2, the manual review configuration, the
placement summaries, and the filled review sheet. Each has a `.public` or summary
counterpart, and hash pins always name the local original. A clean clone therefore
cannot rerun the pilot without a licensed acquisition and those originals, which is
the intended limit.

## Rules for new work

1. Never commit a value read from the acquired RegulonDB files for a named record.
2. Never put such a value in a log, finding, test, figure, or report that is tracked.
3. Keep the acquired data off remote servers unless UNAM agrees, since clause 3.1
   covers servers and networks.
4. `tests/test_regulondb_restricted.py` fails if a restricted file becomes tracked.

## Owner actions

These need the project owner and cannot be settled in the repository:

1. Confirm that the acquisition falls under an accepted agreement, and record the
   date, since the term is one year.
2. Ask CCG-UNAM in writing whether the thesis and any data release may use the
   controls, because they were selected with an exclusion set built from RegulonDB
   and clause 3.2 restricts derivative works.
3. Ask the same contact whether aggregate statistics and TSS-support results may be
   published.
4. Cite the RegulonDB publication named in the terms in the thesis and papers.
