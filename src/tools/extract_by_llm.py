"""
extract_by_llm tool - Extract specific fields from unstructured text.

Implements semantic field extraction with optional structured output.
Stage 2.1: Added schema validation, type coercion, and retry logic.
"""

import json
from typing import List, Dict, Any, Optional
from ..services import InputNormalizer, get_llm_client, SchemaValidator, TypeCoercer


async def extract_by_llm(
    input: List[Any],
    fields: Optional[List[str]] = None,
    response_format: Optional[Dict[str, Any]] = None,
    args: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Extract specific fields from unstructured text using LLM.

    Args:
        input: List of items to extract from
        fields: List of field names to extract (required if response_format not provided)
        response_format: JSON Schema for structured output (OpenAI-compatible)
        args: Optional config dict with:
            - model: Override default model
            - temperature: Override temperature
            - max_tokens: Override max_tokens
            - prompt: Custom extraction instructions

    Returns:
        List of {id, result, error?} dicts where result is dict with extracted fields

    Examples:
        >>> # Simple field extraction
        >>> result = await extract_by_llm(
        ...     input=["Article by Wade on 2025-10-12"],
        ...     fields=["author", "date"]
        ... )
        >>> # [{"id": 0, "result": {"author": "Wade", "date": "2025-10-12"}}]

        >>> # Structured output with arrays
        >>> result = await extract_by_llm(
        ...     input=["Authors: Wade, Smith. Tags: AI, tech"],
        ...     response_format={
        ...         "type": "object",
        ...         "properties": {
        ...             "authors": {"type": "array", "items": {"type": "string"}},
        ...             "tags": {"type": "array", "items": {"type": "string"}}
        ...         }
        ...     }
        ... )
        >>> # [{
        >>> #   "id": 0,
        >>> #   "result": {
        >>> #     "authors": ["Wade", "Smith"],
        >>> #     "tags": ["AI", "tech"]
        >>> #   }
        >>> # }]
    """
    # Validate inputs
    if not fields and not response_format:
        raise ValueError("Either 'fields' or 'response_format' must be provided")

    if fields and not isinstance(fields, list):
        raise ValueError("fields must be a list")

    if fields and len(fields) == 0:
        raise ValueError("fields list cannot be empty")

    # Normalize input
    normalized = InputNormalizer.normalize(input)

    # Extract args
    model = args.get("model") if args else None
    temperature = args.get("temperature", 0.0) if args else 0.0
    max_tokens = args.get("max_tokens", 1000) if args else 1000
    custom_prompt = args.get("prompt") if args else None
    max_retries = args.get("max_retries", 2) if args else 2  # Stage 2.1: Add retry support
    enable_coercion = args.get("enable_coercion", True) if args else True  # Stage 2.1: Add type coercion

    # Get LLM client
    llm_client = get_llm_client()

    # Determine extraction mode
    use_structured_output = response_format is not None

    # Process each item
    results = []

    for item in normalized:
        try:
            # Convert data to string
            text = str(item["data"])

            if use_structured_output:
                # Use structured output mode with retry logic (Stage 2.1)
                system_prompt = """You are a data extraction expert. Extract information according to the provided schema.

Rules:
- Follow the schema structure exactly
- Use correct data types (string, number, array, object, boolean)
- If a field is not found and not required, you may omit it or use null
- Ensure all required fields are present"""

                if custom_prompt:
                    system_prompt += f"\n\nAdditional instructions: {custom_prompt}"

                user_prompt = f"Extract information from the following text:\n\n{text}"

                # Retry loop for schema validation (Stage 2.1)
                result_data = None
                last_error = None

                for attempt in range(max_retries + 1):
                    try:
                        # Call with structured output
                        result_data = await llm_client.structured_output(
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            schema=response_format,
                            model=model,
                            temperature=temperature
                        )

                        # Stage 2.1: Apply type coercion if enabled
                        if enable_coercion and isinstance(result_data, dict):
                            result_data = TypeCoercer.coerce_object_to_schema(result_data, response_format)

                        # Stage 2.1: Validate against schema
                        is_valid, error_msg = SchemaValidator.validate(result_data, response_format)

                        if is_valid:
                            break  # Success, exit retry loop

                        # Validation failed, prepare retry
                        if attempt < max_retries:
                            # Get detailed validation errors
                            validation_result = SchemaValidator.validate_with_details(result_data, response_format)
                            error_feedback = SchemaValidator.create_error_feedback(
                                result_data, response_format, validation_result["errors"]
                            )

                            # Update user prompt with error feedback
                            user_prompt = f"{user_prompt}\n\n{error_feedback}"
                            last_error = error_msg
                        else:
                            last_error = error_msg

                    except Exception as e:
                        last_error = str(e)
                        if attempt >= max_retries:
                            raise

                # If still invalid after retries, log warning but return data
                if last_error:
                    # Include validation error in result but still return the data
                    results.append({
                        "id": item["id"],
                        "result": result_data,
                        "error": f"Schema validation warning: {last_error}"
                    })
                    continue

            else:
                # Use simple field extraction mode
                fields_str = ", ".join(fields)
                system_prompt = """You are a data extraction expert. Extract specific fields from unstructured text.

Rules:
- Extract exactly the fields specified
- If a field is not found, use null
- Return result as JSON object with field names as keys
- Be accurate and precise in extraction"""

                if custom_prompt:
                    system_prompt += f"\n\nAdditional instructions: {custom_prompt}"

                user_prompt = f"Fields to extract: {fields_str}\n\nText:\n{text}\n\nExtracted data (as JSON):"

                # Call LLM
                response = await llm_client.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Parse JSON response
                try:
                    result_data = json.loads(response.strip())
                except json.JSONDecodeError:
                    # Fallback: create dict from response text
                    result_data = {}
                    for field in fields:
                        if field.lower() in response.lower():
                            # Very simple extraction fallback
                            result_data[field] = None

            results.append({"id": item["id"], "result": result_data})

        except Exception as e:
            results.append({
                "id": item["id"],
                "result": None,
                "error": str(e)
            })

    return results
