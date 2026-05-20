I choose the embedding model based on the retrieval quality, data sensitivity, and operational constraints

## 3️⃣ Embedding quality (how I evaluate)

I don’t just “trust the model”.

I evaluate using:

* **Recall@K**
* **MRR**
* Human judgment on top retrieved chunks

Say:

> “I build a small evaluation set of real user questions and check whether the correct chunks are retrieved in top-K.”

RAG failures happen at retrieval.

text-embedding-3-large

2️⃣ Sentence Transformers (self-hosted):

* `all-MiniLM-L6-v2`
* `multi-qa-mpnet-base-dot-v1`



NVIDIA NV‑Embed‑v2


### **Open‑source, self‑hosted options**

* **BGE‑M3** — strong general performance and hybrid retrieval support, ~8K token window.
* **E5 family (Microsoft)** — top open embedding models, but usually typical context windows (smaller) unless extended.
