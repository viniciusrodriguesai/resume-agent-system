# Presentation Script

## 1. Problem

Keyword matching does not understand many equivalent descriptions and usually
does not explain why a score was produced.

## 2. Solution

The application uses specialized agents to anonymize documents, structure the
resume and job, retrieve evidence, rerank passages, calculate scores, review
borderline cases, produce recommendations, and generate reports.

## 3. Main demonstration

1. Upload or paste a resume.
2. Upload or paste a job.
3. Run the analysis.
4. Show the privacy report.
5. Show the best evidence for each requirement.
6. Show the retrieval engine and reranker.
7. Show the Review Agent loop.
8. Download the report.
9. Open the local analysis history.

## 4. AI comparison

Explain that the system can compare:

- lexical TF-IDF fallback;
- multilingual embeddings;
- embeddings plus CrossEncoder reranking.

## 5. Limitations

The model may misunderstand ambiguous sentences, parsing may fail on complex
layouts, the skill catalog may be incomplete, and historical language patterns
may contain bias. Therefore, the tool supports human analysis and does not make
the hiring decision.
