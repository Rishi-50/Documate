# Project AI Assistant

The assistant answers questions using OCR text from successfully processed
documents in the selected project. It retrieves the most relevant text chunks,
asks Gemini to answer from those excerpts, and returns document/page citations.
If no processed chunks are available, it asks the user to process documents
before trying again.

## Processing and retrieval

1. The upload pipeline runs OCR and document intelligence.
2. The existing organization stage completes, then `EmbeddingService` divides
   each OCR page into overlapping text chunks and
   creates Gemini `RETRIEVAL_DOCUMENT` embeddings.
3. Chunk text, page number, document relation, and vector are stored in the
   `DocumentEmbedding` table in the existing Django database.
4. A project question is embedded as `RETRIEVAL_QUERY`. Cosine similarity ranks
   only chunks belonging to successfully processed documents in that project.
5. The assistant receives the question and retrieved excerpts and returns an
   answer with source labels and links to the source documents.

No separate vector database is required.

## Configuration and setup

Set `GEMINI_API_KEY` in the environment (the existing document-intelligence
pipeline uses the same key), then apply database migrations:

```powershell
.\venv\Scripts\python.exe manage.py migrate
```

New uploads are indexed as part of normal document processing. Previously
uploaded documents must be reprocessed to create embeddings before the assistant
can search them.

## Project question endpoint

The project detail page submits a CSRF-protected form to:

```text
POST /project/<project_id>/assistant/
```

Form field:

```text
question=<question, up to 2000 characters>
```

Successful responses contain an `answer` and a `sources` array with a source
label, document name, optional page number, and document-detail URL. Invalid
questions return HTTP 400; upstream assistant failures return HTTP 502.

## Tests

Run the AI assistant and indexing tests with:

```powershell
.\venv\Scripts\python.exe manage.py test ai_processing.test
```
