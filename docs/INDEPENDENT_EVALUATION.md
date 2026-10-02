# Independent annotation handoff

Use fictional inputs or properly consented/deidentified source material. Do not publish personal names, contact details, addresses or confidential employment documents.

Format: JSON object with `name`, `annotation_origin` and `cases`; each case has unique `id`, `category`, `resume`, `requirement` and `expected` (`matched`, `partial`, `missing`). Each case must represent exactly one requirement.

Rubric: matched requires explicit evidence for every mandatory concept and required context. Partial means relevant evidence exists but at least one capability is incomplete. Missing means no relevant evidence or an explicit contradiction. For hard predicates such as current enrollment, decide in advance whether a missing component counts as partial or missing. This boundary caused all six disagreements in the internal challenge.

Prefer two independent annotators and a third adjudicator for disagreements. Preserve each initial label and the final adjudication; document agreement, label counts, languages and experience contexts. The included blank [handoff template](../evaluation/challenge/independent-template.json) does not contain valid annotations and cannot be evaluated until an external reviewer fills it.

Keep a development set separate from the protected evaluation set. Freeze the source revision, model configuration, rubric and dataset hash before evaluating. Record whether the annotators or developer previously viewed the evaluation labels. No contact with external people is performed by this repository.
