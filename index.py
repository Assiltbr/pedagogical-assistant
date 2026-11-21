import sys
from src.ingestion import ingest
from src.vectorstore import add_chunks

chunks = ingest(sys.argv[1])
print("Indexed", add_chunks(chunks), "new chunks of", len(chunks))