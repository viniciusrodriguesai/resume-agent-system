# Host the lexical Streamlit demonstration

`render.yaml` declares one **free** Render Python web service, using the existing Streamlit application and its actual analysis pipeline. It disables optional model downloads, history and result caching. It uses Render's assigned PORT, a health endpoint, lower input limits and error-level logging. No secret is needed.

1. Connect the repository to Render and create a Blueprint from `render.yaml`.
2. Confirm the service plan is Free; do not provision paid resources implicitly.
3. Wait for deployment, then verify `/_stcore/health` and run the fictional sample in the interface.
4. Inspect enrollment and deployment evidence before sharing the actual URL.
5. Add a live link only after that deployed instance passes verification.

Free instances can sleep when idle and have ephemeral storage. Heavy embeddings/reranking are deliberately disabled. The demo is not a validated hiring system. Prefer fictional or already deidentified inputs; do not submit confidential resumes. Disabled history/cache prevents those storage paths, but is not a guarantee against infrastructure logs or transient browser/server processing.

The blueprint passed the official Render JSON schema; the actual Streamlit application was started locally and its health endpoint returned ok. No successful public deployment is claimed until a real service URL has been verified.

[Render free service limits](https://render.com/docs/free) · [Blueprint reference](https://render.com/docs/blueprint-spec).
