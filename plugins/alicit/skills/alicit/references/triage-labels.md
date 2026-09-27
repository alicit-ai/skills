# Triage labels

The engineering skills use five canonical triage roles. This repository maps
them directly to GitHub labels:

| Skill role | GitHub label | Meaning |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | A maintainer must classify and reproduce the report. |
| `needs-info` | `needs-info` | Progress requires specific missing evidence from the reporter. |
| `ready-for-agent` | `ready-for-agent` | Scope and acceptance criteria are precise enough for an implementation agent. |
| `ready-for-human` | `ready-for-human` | The next step requires a person, hardware interaction, or external authority. |
| `wontfix` | `wontfix` | The maintainers have decided the report will not be actioned. |

When a skill names a canonical role, use the matching GitHub label. Resolution
labels such as `duplicate` and `invalid` retain their ordinary meaning. Do not
use readiness labels as priority labels.

## Priority

Priority is a separate axis. An open issue has at most one priority label:

| GitHub label | Meaning |
| --- | --- |
| `P0` | It blocks the beta or production now. |
| `P1` | It is the next work after the `P0` issues. |
| `P2` | It is in the backlog. |

Readiness and priority stay separate. A `ready-for-agent` issue can be `P2`,
and a `P0` issue can still be `needs-info`. A change to one label does not
change the other.
