# Portfolio Summary Sequence Diagram

This diagram shows the technical flow for answering "What should I know about my portfolio today?" using GraphQL (Node.js server), semantic search, and summarization.

```mermaid
sequenceDiagram
  participant User
  participant Frontend
  participant GraphQL
  participant FastAPI
  participant ChromaDB
  participant MarketAPI
  participant NewsAPI/DB

  User->>Frontend: "What should I know about my portfolio today?"
  Frontend->>GraphQL: query portfolio
  GraphQL->>MarketAPI: fetch prices
  GraphQL->>NewsAPI/DB: fetch news
  GraphQL->>ChromaDB: semantic search for relevant news
  GraphQL->>FastAPI: summarize news
  FastAPI-->>GraphQL: summary text
  ChromaDB-->>GraphQL: relevant news IDs
  MarketAPI-->>GraphQL: price data
  NewsAPI/DB-->>GraphQL: news articles
  GraphQL->>Frontend: summary + stats
  Frontend->>User: display answer
``` 