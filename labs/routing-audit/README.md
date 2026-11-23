# Multilingual support routing audit

A fictional customer support service routes reports of account compromise and unauthorized or duplicate payments to a review queue. Other messages go to the routine queue. This case study measures how phrase coverage affects review routing across English, Roman Urdu, and Urdu.

## Run the audit

Run `make demo` from this directory with Python 3.9+ and Make. It runs four tests and prints the overall and per-language confusion counts, followed by the misclassified fixture IDs. With Python alone, run `python3 -B -m unittest -v` and then `python3 -B audit.py`.

## Setup

The baseline matches three English phrases with word boundaries and case folding. The revision adds six phrases across Roman Urdu and Urdu. It also normalizes Unicode, maps selected Urdu character variants, strips combining marks, and treats punctuation as a separator.

The 18 messages in [fixtures.json](fixtures.json) are fictional examples with explicit expected queue labels. Each language has six fixtures. Labels depend on what the message reports. For example, the Roman Urdu question that rules out an account compromise is labelled routine. The fixtures exercise the rules and their known limitations, so the results describe this sample only.

## Results

A positive prediction means routing to the review queue.

| Language | Policy | True positives | False positives | True negatives | False negatives |
| --- | --- | ---: | ---: | ---: | ---: |
| All | Baseline | 3 | 0 | 8 | 7 |
| All | Revised | 9 | 1 | 7 | 1 |
| English | Baseline | 3 | 0 | 2 | 1 |
| English | Revised | 3 | 0 | 2 | 1 |
| Roman Urdu | Baseline | 0 | 0 | 3 | 3 |
| Roman Urdu | Revised | 3 | 1 | 2 | 0 |
| Urdu | Baseline | 0 | 0 | 3 | 3 |
| Urdu | Revised | 3 | 0 | 3 | 0 |

The revision sends six additional review-worthy messages to review and adds one unnecessary review. Review recall rises from 3/10 to 9/10 and review precision falls from 3/3 to 9/10. The extra review comes from `ru05`, where the message contains a matched clause and then rules it out. Both versions miss `en04`, an English report that describes an unknown device changing the password without using a covered phrase.

## Consent behavior

`route()` returns the internal queue and a Boolean that controls whether a review handoff may include the transcript. Only an explicit Boolean `True` on a review decision permits sharing. Omitted consent, `False`, and values such as the string `"true"` and the integer `1` all keep sharing disabled. The caller supplies consent through structured metadata. Message text alone can never set it, and switching consent never changes the selected queue.

The audit emits only aggregate counts and synthetic fixture IDs. The example has no transport or persistence layer. A caller integrating the decision is responsible for enforcing the sharing flag at the point of handoff.
