"""
Batch processing service for parallel execution with error handling.
"""

import asyncio
import time
from typing import List, Dict, Any, Callable, Awaitable
from ..models import OutputItem, ProcessMetadata


async def batch_process(
    items: List[Dict[str, Any]],
    operation: Callable[[Dict[str, Any]], Awaitable[Any]],
    max_concurrent: int = 5
) -> tuple[List[OutputItem], ProcessMetadata]:
    """
    Process items in parallel with concurrency limit and error handling.

    Args:
        items: List of normalized items {id, data}
        operation: Async function to process each item
        max_concurrent: Max concurrent operations (default: 5)

    Returns:
        Tuple of (results, metadata)
        - results: List of OutputItem objects
        - metadata: ProcessMetadata with stats

    Example:
        >>> async def process_item(item):
        ...     return await llm_client.chat([{"role": "user", "content": item["data"]}])
        >>> results, metadata = await batch_process(items, process_item, max_concurrent=10)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    start_time = time.time()

    async def process_with_semaphore(item: Dict[str, Any]) -> OutputItem:
        """Process single item with semaphore and error handling."""
        async with semaphore:
            try:
                result = await operation(item)
                return OutputItem(id=item["id"], result=result)
            except Exception as e:
                return OutputItem(id=item["id"], result=None, error=str(e))

    # Process all items concurrently (up to max_concurrent)
    tasks = [process_with_semaphore(item) for item in items]
    results = await asyncio.gather(*tasks)

    # Calculate metadata
    end_time = time.time()
    processing_time_ms = (end_time - start_time) * 1000

    successful = sum(1 for r in results if r.error is None)
    failed = len(results) - successful

    metadata = ProcessMetadata(
        total_items=len(items),
        successful=successful,
        failed=failed,
        processing_time_ms=processing_time_ms
    )

    return results, metadata


async def batch_process_simple(
    items: List[Dict[str, Any]],
    operation: Callable[[Dict[str, Any]], Awaitable[Any]]
) -> List[OutputItem]:
    """
    Simple batch processing (sequential, no metadata).

    Args:
        items: List of normalized items
        operation: Async function to process each item

    Returns:
        List of OutputItem objects

    Example:
        >>> results = await batch_process_simple(items, process_item)
    """
    results = []

    for item in items:
        try:
            result = await operation(item)
            results.append(OutputItem(id=item["id"], result=result))
        except Exception as e:
            results.append(OutputItem(id=item["id"], result=None, error=str(e)))

    return results
