# SkillSpan external component evaluation protocol v1

Registered before retrieving or scoring the published test split. The production catalog and extractor remain unchanged. This evaluates **skill mention detection**, not resume/job compatibility, enrollment reasoning, candidate ranking or hiring validity.

## Source

Zhang, Jensen, Sonniks and Plank (NAACL 2022), SkillSpan: Hard and Soft Skill Extraction from English Job Postings, https://aclanthology.org/2022.naacl-main.366/; official data https://github.com/kris927b/SkillSpan, MIT license. Use the complete published `data/json/test.json` (both released sources, house and tech); do not select only technical sentences. Record upstream revision and file SHA-256. Existing human BIO annotations are external to this project. They were not commissioned as a blinded evaluation of this system, and pretrained models may have seen public data.

## Adapter and metrics

Input to unchanged `detect_skills`: sentence tokens joined with spaces. Localize the aliases of names returned by that function to contiguous token windows using the production normalizer. Use minimal matching windows and merge their token indices. The system returns canonical skills, not BIO spans; these are **adapter token metrics**, not native exact-span SkillSpan leaderboard scores.

Gold positives: union of all non-O tokens in `tags_skill` and `tags_knowledge`. Primary metrics: micro token precision, recall, F1 across all sentences. Also report each source, total gold tokens/spans, missed tokens, predicted tokens, false-positive tokens, and fully covered gold spans. Do not restrict the recall denominator to this project's catalog. Merge overlapping gold spans for span coverage; never relabel human annotations. Publish counts and metrics, not copied job text.

Cluster bootstrap 500 replicates with seed 20261002 over (source, posting idx); percentile 95% intervals for P/R/F1. Repeated sentences within a posting are not independent observations. No development on test, no catalog expansion after seeing test under v1, no optional embedding/reranking comparison on this extraction component (those models act downstream).

## Scope and remaining work

This supplies externally annotated component evidence beyond the 36 internal synthetic matching cases. It cannot replace independently annotated real resume/job pairs for the full matched/partial/missing task. Keep the previous ablation: optional models did not improve those 36 labels. Default lexical operation is justified by that bounded evidence, not a claim that semantic models never help. Full-pipeline evaluation still requires consented or publicly licensed pairs and independent reviewers/adjudication.
