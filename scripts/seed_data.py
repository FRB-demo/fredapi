#!/usr/bin/env python3
"""Seed script to run initial scraping and ingestion for all configured sources.

Usage:
    python scripts/seed_data.py [--source SOURCE_NAME]

Without --source, scrapes and ingests all configured sources.
"""

import argparse
import logging
import sys

# Add project root to path
sys.path.insert(0, ".")

from app.config import get_settings
from app.processing.chunker import chunk_text
from app.processing.pdf_parser import PDFParseError, parse_pdf
from app.scrapers.registry import SCRAPER_REGISTRY, get_all_sources, get_scraper
from app.storage.document_store import DocumentStore
from app.storage.vector_store import VectorStore
from app.utils.text import clean_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def ingest_source(source_name: str, vector_store: VectorStore, doc_store: DocumentStore) -> dict:
    """Scrape and ingest a single source.

    Returns:
        Dict with counts of documents found, ingested, and errors.
    """
    logger.info(f"Processing source: {source_name}")

    scraper = get_scraper(source_name)
    result = {"found": 0, "ingested": 0, "errors": []}

    # Scrape
    try:
        documents = scraper.scrape()
        result["found"] = len(documents)
        logger.info(f"  Found {len(documents)} documents")
    except Exception as e:
        logger.error(f"  Scraper failed: {e}")
        result["errors"].append(str(e))
        return result

    # Ingest each document
    for doc in documents:
        try:
            if doc_store.document_exists(doc.url):
                logger.info(f"  Skipping (already ingested): {doc.title}")
                continue

            # Parse
            if doc.local_path and doc.doc_type == "pdf":
                text = parse_pdf(doc.local_path)
            elif doc.content:
                text = doc.content
            else:
                logger.warning(f"  No content for: {doc.title}")
                continue

            # Clean and chunk
            text = clean_text(text)
            metadata = {
                "source": doc.source_name,
                "url": doc.url,
                "title": doc.title,
                "date": doc.date or "",
                "doc_type": doc.doc_type,
            }
            chunks = chunk_text(text, metadata=metadata)

            # Store
            vector_store.add_chunks(chunks)
            doc_store.add_document(
                source_name=doc.source_name,
                url=doc.url,
                title=doc.title,
                date=doc.date,
                doc_type=doc.doc_type,
                local_path=doc.local_path,
                chunk_count=len(chunks),
            )

            result["ingested"] += 1
            logger.info(f"  Ingested: {doc.title} ({len(chunks)} chunks)")

        except PDFParseError as e:
            logger.error(f"  Parse error for {doc.title}: {e}")
            result["errors"].append(str(e))
        except Exception as e:
            logger.error(f"  Error ingesting {doc.title}: {e}")
            result["errors"].append(str(e))

    return result


def main():
    parser = argparse.ArgumentParser(description="Seed data by scraping and ingesting sources")
    parser.add_argument(
        "--source",
        type=str,
        help="Specific source to scrape (default: all sources)",
    )
    args = parser.parse_args()

    settings = get_settings()

    # Initialize stores
    vector_store = VectorStore(
        persist_directory=settings.chroma_db_path,
        embedding_model=settings.embedding_model,
    )
    doc_store = DocumentStore(db_path=settings.sqlite_db_path)

    # Determine which sources to process
    if args.source:
        source_names = [args.source]
    else:
        source_names = list(SCRAPER_REGISTRY.keys())

    logger.info(f"Seeding data for sources: {source_names}")

    # Process each source
    total_results = {"found": 0, "ingested": 0, "errors": []}
    for name in source_names:
        result = ingest_source(name, vector_store, doc_store)
        total_results["found"] += result["found"]
        total_results["ingested"] += result["ingested"]
        total_results["errors"].extend(result["errors"])

    # Summary
    logger.info("=== Seed Complete ===")
    logger.info(f"  Documents found:    {total_results['found']}")
    logger.info(f"  Documents ingested: {total_results['ingested']}")
    logger.info(f"  Errors:             {len(total_results['errors'])}")

    stats = vector_store.get_stats()
    logger.info(f"  Total chunks in store: {stats['total_chunks']}")
    logger.info(f"  Sources in store:      {stats['sources']}")

    if total_results["errors"]:
        logger.warning("Errors encountered:")
        for err in total_results["errors"]:
            logger.warning(f"  - {err}")


if __name__ == "__main__":
    main()
