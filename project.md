***Data Ingestion & Indexing***

For data ingestion, we use a time-triggered Azure Function App that runs daily at 4:00 AM to ensure fresh dividend data for the upcoming four-week window.

The function invokes a FastAPI backend responsible for orchestrating the data pipeline. The backend first retrieves dividend schedules from Nasdaq APIs, and for each dividend record, it calls Finnhub to enrich the data with market capitalization and the previous trading day’s closing price.

We apply business filters early in the pipeline, excluding companies with a market capitalization below $1B to ensure data relevance and reduce downstream processing cost.

After validation and filtering, we normalize and persist the structured dividend data into PostgreSQL, which acts as the system of record.

For GenAI use cases, the backend transforms each dividend record into a semantic chunk, combining key attributes such as company name, dividend date, yield, market cap, and price context.

These chunks are embedded using Azure OpenAI embedding models, and the resulting vectors are stored in pgvector for traceability and versioning.

Finally, the embedded documents are indexed into Azure Cognitive Search, enabling semantic and vector search for downstream RAG workflows.




The Azure Cognitive Search index is designed to closely mirror the pgvector schema to keep data models consistent across storage and retrieval layers.
For vector search, we configure HNSW (Hierarchical Navigable Small World) as the approximate nearest neighbor algorithm, using cosine similarity as the distance metric, which is well-suited for semantic embeddings.

The index supports hybrid search, allowing vector similarity search to be combined with structured filters—such as market cap thresholds or date ranges—to improve precision and reduce noise.

This design enables low-latency semantic retrieval while maintaining strong filtering capabilities for financial domain queries.





We use both pgvector and Azure Cognitive Search, but for different reasons.

pgvector is mainly our internal storage and control layer. It keeps embeddings close to the source data, makes re-embedding easy when models change, and gives us full SQL-level traceability and versioning.

Azure Cognitive Search is optimized for query-time retrieval. It gives us fast vector search, hybrid filtering, and semantic ranking out of the box, which is hard to replicate efficiently in Postgres.

So in short, pgvector is for persistence and governance, while Cognitive Search is for serving RAG queries at scale.

If the system were simpler, we could use only Cognitive Search—but for enterprise use, the separation gives us more flexibility and control.





For Nasdaq, since it’s a public endpoint, we treat it as best-effort fetch and wrap it with retries and timeouts.

Finnhub has strict rate limits, so we enforce a client-side throttle using a request counter and elapsed time. If we approach the limit, we pause the job to stay within quota.

For embedding and indexing failures, we rely on idempotent batch processing. Each dividend record has a processing status in Postgres—fetched, embedded, indexed.

If Azure OpenAI embedding fails mid-batch, we don’t roll back everything. We persist progress and resume from the last successful record on the next run.

Similarly, if pushing to Azure Cognitive Search fails, we retry only the failed chunks instead of reprocessing the full dataset.

At the orchestration level, Azure Function logs failures and emits alerts, so we can detect partial failures early and rerun safely without duplicating data.

Track status per record, retry only what failed, never reprocess blindly.




When a user submits a question, the backend forwards the query along with a trace ID to the agent executor, which acts as the orchestration layer for retrieval, tool calls, and LLM interaction.


The agent lets the LLM decide whether the query requires retrieval, and if so, it routes the request to the RAG tool.

Inside the RAG tool, we generate an embedding for the user query using the same embedding model as indexing, then run a vector search against Azure Cognitive Search.

The retrieved documents are appended to the conversation as grounding context before calling the LLM for final response generation.



Q2.3 – Hallucination Control)
We control hallucination in two main ways.

First, we use prompt constraints, explicitly instructing the model to answer only based on the retrieved context and to say “not found” if the information isn’t available.

Second, we enforce structured outputs using Pydantic schemas, so the LLM must return data in a predefined format. If the response doesn’t validate, we reject it and retry.

This combination keeps responses grounded in the RAG context and prevents free-form speculation.




Q2.4 – Performance & Cost Control
To keep the system fast and cost-efficient, we take a few practical steps.

First, we cache embeddings or RAG results for frequently asked queries, so the LLM isn’t called repeatedly for the same information.

Second, we use retrieval only when necessary — the agent decides if a query really needs RAG. Simple questions skip retrieval.

Third, we limit token usage when calling Azure OpenAI, both in the context we send and the max tokens allowed, which helps control cost.

Finally, we monitor performance and can batch or throttle expensive queries during peak hours.




“Our agent runs up to 3 reasoning steps. In each step, it decides which tool to call, executes it, observes the results, and appends the observation to the context for the next turn. It stops once it has a clear answer.”




In RAG, retrieval is fast; embeddings are the real throttle