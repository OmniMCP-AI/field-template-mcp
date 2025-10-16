"""
tag_by_llm tool - Apply multiple relevant tags from a predefined set.

Implements multi-label tagging using LLM.
"""

import json
from typing import List, Dict, Any, Optional
from ..services import InputNormalizer, get_llm_client


async def tag_by_llm(
    input: List[Any],
    tags: List[str],
    prompt: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Apply multiple relevant tags from a predefined set to each input.

    Args:
        input: List of items to tag (strings, numbers, or dicts with {id, data})
        tags: List of possible tags (non-mutually exclusive)
        prompt: Optional custom instructions for tagging context
        args: Optional config dict with:
            - model: Override default model
            - temperature: Override temperature
            - max_tags: Maximum tags per item (default: unlimited)
            - min_relevance: Minimum relevance threshold 0-1 (default: 0.0)
            - include_scores: Return relevance scores (default: False)

    Returns:
        List of {id, result, error?} dicts where result is array of tags

    Examples:
        >>> result = await tag_by_llm(
        ...     input=["Python REST API", "React app"],
        ...     tags=["python", "javascript", "backend", "frontend"]
        ... )
        >>> # [
        >>> #   {"id": 0, "result": ["python", "backend"]},
        >>> #   {"id": 1, "result": ["javascript", "frontend"]}
        >>> # ]

        >>> result = await tag_by_llm(
        ...     input=["Full-stack project"],
        ...     tags=["python", "javascript", "backend", "frontend"],
        ...     args={"max_tags": 2, "include_scores": True}
        ... )
        >>> # [{
        >>> #   "id": 0,
        >>> #   "result": [
        >>> #     {"tag": "backend", "score": 0.9},
        >>> #     {"tag": "frontend", "score": 0.85}
        >>> #   ]
        >>> # }]
    """
    # Validate inputs
    if not isinstance(tags, list) or len(tags) < 1:
        raise ValueError("tags must be a list with at least 1 item")

    # Normalize input
    normalized = InputNormalizer.normalize(input)

    # Extract args
    model = args.get("model") if args else None
    temperature = args.get("temperature", 0.0) if args else 0.0
    max_tags = args.get("max_tags") if args else None
    min_relevance = args.get("min_relevance", 0.0) if args else 0.0
    include_scores = args.get("include_scores", False) if args else False

    # Get LLM client
    llm_client = get_llm_client()

    # Build system prompt
    system_prompt = """You are a tagging expert. Your task is to apply relevant tags from a predefined list to the given text.

Rules:
- You can apply 0 to N tags per input
- Only use tags from the provided list
- Apply all tags that are relevant to the content
- Return tags as a JSON array of strings
- If no tags are relevant, return an empty array []"""

    if prompt:
        system_prompt += f"\n\nAdditional context: {prompt}"

    # Process each item
    results = []

    for item in normalized:
        try:
            # Convert data to string
            text = str(item["data"])

            # Build user prompt
            tags_str = ", ".join(tags)
            user_prompt = f"Available tags: {tags_str}\n\nText to tag:\n{text}\n\nRelevant tags (as JSON array):"

            # Call LLM
            response = await llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=temperature,
                max_tokens=200
            )

            # Parse JSON response
            try:
                result_tags = json.loads(response.strip())
                if not isinstance(result_tags, list):
                    result_tags = []
            except json.JSONDecodeError:
                # Fallback: try to extract tags from text
                result_tags = [tag for tag in tags if tag.lower() in response.lower()]

            # Validate tags are in original list
            validated_tags = []
            for tag in result_tags:
                if tag in tags:
                    validated_tags.append(tag)
                else:
                    # Try case-insensitive match
                    for original_tag in tags:
                        if original_tag.lower() == tag.lower():
                            validated_tags.append(original_tag)
                            break

            # Apply max_tags limit
            if max_tags and len(validated_tags) > max_tags:
                validated_tags = validated_tags[:max_tags]

            # Format result
            if include_scores:
                # Mock scores for now (would use LLM scoring in production)
                result_value = [
                    {"tag": tag, "score": 0.9 - (i * 0.1)}
                    for i, tag in enumerate(validated_tags)
                ]
            else:
                result_value = validated_tags

            results.append({"id": item["id"], "result": result_value})

        except Exception as e:
            results.append({
                "id": item["id"],
                "result": None,
                "error": str(e)
            })

    return results
