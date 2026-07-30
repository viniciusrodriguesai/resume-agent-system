# Presentation Script

## Slide 1 — Title

Introduce the topic: a multi-agent system that analyzes a resume and a job description.

Suggested speech:

> Our project uses agent-based programming to solve a common problem: understanding whether a resume matches a job opportunity.

## Slide 2 — Problem

Explain that candidates may struggle to interpret scattered job requirements.

Suggested speech:

> A job description may mix required qualifications, preferred skills, and general expectations. Our system organizes this information automatically.

## Slide 3 — Solution idea

Explain that each agent performs one part of the analysis.

Suggested speech:

> Instead of using one large block of code, the system distributes the work among specialized agents.

## Slide 4 — Architecture

Show the flow from the two inputs to the final response.

Suggested speech:

> The Resume Agent identifies candidate skills. The Job Agent identifies requirements. The Matching Agent then calculates compatibility, and the remaining agents generate and review recommendations.

## Slide 5 — Implementation

Present Python, Streamlit, pandas, and pdfplumber.

Suggested speech:

> The application was developed in Python with a simple Streamlit interface. It accepts pasted text or PDF, TXT, and Markdown files.

## Slide 6 — Demonstration

Run the application using the files in the `examples` directory.

Suggested speech:

> Here we have a sample resume and a sample internship. The system calculates the compatibility percentage and displays strengths, gaps, and recommendations.

## Slide 7 — Expected result

Show the score, matched skills, missing skills, and suggestions.

Suggested speech:

> The result is not only a score. It explains what was found and indicates what the candidate can improve.

## Slide 8 — Conclusion

Explain limitations and future improvements.

Suggested speech:

> The current version uses keywords, but its architecture can evolve to use embeddings, language models, and integrations with real platforms.
