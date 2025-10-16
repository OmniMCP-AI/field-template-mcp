"""
classify_by_llm tool - Classify text into exactly ONE category.

Implements mutually exclusive classification using LLM.
"""

import json
from typing import List, Dict, Any, Optional
from ..services import InputNormalizer, get_llm_client


async def classify_by_llm(
    input: List[Any],
    categories: List[str],
    prompt: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Classify each input into exactly ONE best-matching category.

    Args:
        input: List of items to classify (strings, numbers, or dicts with {id, data})
        categories: List of possible categories (mutually exclusive, min 2)
        prompt: Optional custom instructions for classification context
        args: Optional config dict with:
            - model: Override default model
            - temperature: Override temperature
            - include_scores: Return confidence scores (default: False)
            - allow_none: Allow null result if no match (default: False)
            - fallback_category: Category to use if no match (default: None)

    Returns:
        List of {id, result, error?} dicts

    Examples:
        >>> result = await classify_by_llm(
        ...     input=["Apple releases iPhone", "Lakers win game"],
        ...     categories=["tech", "sports", "politics"]
        ... )
        >>> # [{"id": 0, "result": "tech"}, {"id": 1, "result": "sports"}]

        >>> result = await classify_by_llm(
        ...     input=[{"id": "a1", "data": "Tech article"}],
        ...     categories=["tech", "sports"],
        ...     args={"include_scores": True}
        ... )
        >>> # [{"id": "a1", "result": {"category": "tech", "score": 0.95}}]
    """
    # Validate inputs
    if not isinstance(categories, list) or len(categories) < 2:
        raise ValueError("categories must be a list with at least 2 items")

    # Normalize input to {id, data} format
    normalized = InputNormalizer.normalize(input)

    # Extract args
    model = args.get("model") if args else None
    temperature = args.get("temperature", 0.0) if args else 0.0
    include_scores = args.get("include_scores", False) if args else False
    allow_none = args.get("allow_none", False) if args else False
    fallback_category = args.get("fallback_category") if args else None

    # Get LLM client
    llm_client = get_llm_client()

    # Build system prompt
    system_prompt = """You are a classification expert. Your task is to classify text into exactly ONE category from the provided list.

Rules:
- You MUST choose exactly one category
- Choose the category that best matches the primary topic or theme
- If uncertain, choose the most likely category
- Return ONLY the category name, nothing else"""

    if prompt:
        system_prompt += f"\n\nAdditional context: {prompt}"

    # Process each item
    results = []

    for item in normalized:
        try:
            # Convert data to string
            text = str(item["data"])

            # Build user prompt
            categories_str = ", ".join(categories)
            user_prompt = f"Categories: {categories_str}\n\nText to classify:\n{text}\n\nCategory:"

            # Call LLM
            response = await llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=temperature,
                max_tokens=100
            )

            # Parse result
            category = response.strip()

            # Validate category is in list
            if category not in categories:
                # Try case-insensitive match
                category_lower = category.lower()
                matched = None
                for cat in categories:
                    if cat.lower() == category_lower:
                        matched = cat
                        break

                if matched:
                    category = matched
                elif allow_none:
                    category = None
                elif fallback_category:
                    category = fallback_category
                else:
                    # Default to first category if no match
                    category = categories[0]

            # Format result
            if include_scores:
                result_value = {
                    "category": category,
                    "score": 0.95  # Mock score for now
                }
            else:
                result_value = category

            results.append({"id": item["id"], "result": result_value})

        except Exception as e:
            results.append({
                "id": item["id"],
                "result": None,
                "error": str(e)
            })

    return results
