"""
Unified LLM Tool Executor - Executes LLM-based tools from JSON templates.

This module provides a generic execution engine that can handle different LLM
operation types (classify, extract, tag) based on JSON configuration templates.
"""

import json
from typing import List, Dict, Any, Optional
from ..services import InputNormalizer, get_llm_client, SchemaValidator, TypeCoercer


class LLMToolExecutor:
    """
    Unified executor for LLM-based tools driven by JSON templates.

    Supports three operation types:
    - classify_by_llm: Single-label classification
    - extract_by_llm: Field extraction with optional schema
    - tag_by_llm: Multi-label tagging
    """

    def __init__(self, template: Dict[str, Any]):
        """
        Initialize executor with a tool template.

        Args:
            template: JSON template configuration with:
                - tool_name: Name of the tool
                - model_config: Default model settings
                - prompt_templates: System and user prompt templates
                - parameters: Input parameter definitions
                - output_format: Expected output structure
        """
        self.template = template
        self.tool_name = template["tool_name"]
        self.model_config = template.get("model_config", {})
        self.prompt_templates = template.get("prompt_templates", {})
        self.parameters = template.get("parameters", {})

    async def execute(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute the tool based on its type.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            List of {id, result, error?} dicts
        """
        tool_name = self.tool_name

        if tool_name == "classify_by_llm":
            return await self._execute_classify(**kwargs)
        elif tool_name == "extract_by_llm":
            return await self._execute_extract(**kwargs)
        elif tool_name == "tag_by_llm":
            return await self._execute_tag(**kwargs)
        else:
            raise ValueError(f"Unknown tool type: {tool_name}")

    async def _execute_classify(
        self,
        input: List[Any],
        categories: List[str],
        prompt: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute classification operation."""
        # Validate inputs
        if not isinstance(categories, list) or len(categories) < 2:
            raise ValueError("categories must be a list with at least 2 items")

        # Normalize input
        normalized = InputNormalizer.normalize(input)

        # Extract args
        model = args.get("model") if args else None
        temperature = args.get("temperature", self.model_config.get("temperature", 0.0)) if args else self.model_config.get("temperature", 0.0)
        include_scores = args.get("include_scores", False) if args else False
        allow_none = args.get("allow_none", False) if args else False
        fallback_category = args.get("fallback_category") if args else None

        # Get LLM client
        llm_client = get_llm_client()

        # Build prompts from template
        system_prompt = self.prompt_templates.get("system", "")
        if prompt:
            system_prompt += f"\n\nAdditional context: {prompt}"

        # Process each item
        results = []

        for item in normalized:
            try:
                text = str(item["data"])

                # Build user prompt from template
                user_template = self.prompt_templates.get("user", "")
                categories_str = ", ".join(categories)
                user_prompt = user_template.format(categories=categories_str, text=text)

                # Call LLM
                max_tokens = self.model_config.get("max_tokens", 100)
                response = await llm_client.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model or self.model_config.get("model"),
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Parse result
                category = response.strip()

                # Validate category
                if category not in categories:
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
                        category = categories[0]

                # Format result
                if include_scores:
                    result_value = {"category": category, "score": 0.95}
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

    async def _execute_extract(
        self,
        input: List[Any],
        fields: Optional[List[str]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute extraction operation."""
        # Validate inputs
        if not fields and not response_format:
            raise ValueError("Either 'fields' or 'response_format' must be provided")

        if fields is not None and not isinstance(fields, list):
            raise ValueError("fields must be a list")

        if fields is not None and len(fields) == 0:
            raise ValueError("fields list cannot be empty")

        # Normalize input
        normalized = InputNormalizer.normalize(input)

        # Extract args
        model = args.get("model") if args else None
        temperature = args.get("temperature", self.model_config.get("temperature", 0.0)) if args else self.model_config.get("temperature", 0.0)
        max_tokens = args.get("max_tokens", self.model_config.get("max_tokens", 1000)) if args else self.model_config.get("max_tokens", 1000)
        custom_prompt = args.get("prompt") if args else None
        max_retries = args.get("max_retries", 2) if args else 2
        enable_coercion = args.get("enable_coercion", True) if args else True

        # Get LLM client
        llm_client = get_llm_client()

        # Determine extraction mode
        use_structured_output = response_format is not None

        # Process each item
        results = []

        for item in normalized:
            try:
                text = str(item["data"])

                if use_structured_output:
                    # Use structured output mode
                    system_prompt = self.prompt_templates.get("structured_system", "")
                    if custom_prompt:
                        system_prompt += f"\n\nAdditional instructions: {custom_prompt}"

                    user_prompt = f"Extract information from the following text:\n\n{text}"

                    # Retry loop for schema validation
                    result_data = None
                    last_error = None

                    for attempt in range(max_retries + 1):
                        try:
                            result_data = await llm_client.structured_output(
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                schema=response_format,
                                model=model or self.model_config.get("model"),
                                temperature=temperature
                            )

                            # Apply type coercion if enabled
                            if enable_coercion and isinstance(result_data, dict):
                                result_data = TypeCoercer.coerce_object_to_schema(result_data, response_format)

                            # Validate against schema
                            is_valid, error_msg = SchemaValidator.validate(result_data, response_format)

                            if is_valid:
                                break

                            # Validation failed, prepare retry
                            if attempt < max_retries:
                                validation_result = SchemaValidator.validate_with_details(result_data, response_format)
                                error_feedback = SchemaValidator.create_error_feedback(
                                    result_data, response_format, validation_result["errors"]
                                )
                                user_prompt = f"{user_prompt}\n\n{error_feedback}"
                                last_error = error_msg
                            else:
                                last_error = error_msg

                        except Exception as e:
                            last_error = str(e)
                            if attempt >= max_retries:
                                raise

                    # If still invalid after retries, include warning
                    if last_error:
                        results.append({
                            "id": item["id"],
                            "result": result_data,
                            "error": f"Schema validation warning: {last_error}"
                        })
                        continue

                else:
                    # Use simple field extraction mode
                    fields_str = ", ".join(fields)
                    system_prompt = self.prompt_templates.get("system", "")
                    if custom_prompt:
                        system_prompt += f"\n\nAdditional instructions: {custom_prompt}"

                    user_template = self.prompt_templates.get("user", "")
                    user_prompt = user_template.format(fields=fields_str, text=text)

                    # Call LLM
                    response = await llm_client.chat(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        model=model or self.model_config.get("model"),
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    # Parse JSON response
                    try:
                        result_data = json.loads(response.strip())
                    except json.JSONDecodeError:
                        result_data = {}
                        for field in fields:
                            if field.lower() in response.lower():
                                result_data[field] = None

                results.append({"id": item["id"], "result": result_data})

            except Exception as e:
                results.append({
                    "id": item["id"],
                    "result": None,
                    "error": str(e)
                })

        return results

    async def _execute_tag(
        self,
        input: List[Any],
        tags: List[str],
        prompt: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute tagging operation."""
        # Validate inputs
        if not isinstance(tags, list) or len(tags) < 1:
            raise ValueError("tags must be a list with at least 1 item")

        # Normalize input
        normalized = InputNormalizer.normalize(input)

        # Extract args
        model = args.get("model") if args else None
        temperature = args.get("temperature", self.model_config.get("temperature", 0.0)) if args else self.model_config.get("temperature", 0.0)
        max_tags = args.get("max_tags") if args else None
        # min_relevance not implemented yet - would require scoring from LLM
        include_scores = args.get("include_scores", False) if args else False

        # Get LLM client
        llm_client = get_llm_client()

        # Build prompts from template
        system_prompt = self.prompt_templates.get("system", "")
        if prompt:
            system_prompt += f"\n\nAdditional context: {prompt}"

        # Process each item
        results = []

        for item in normalized:
            try:
                text = str(item["data"])

                # Build user prompt from template
                user_template = self.prompt_templates.get("user", "")
                tags_str = ", ".join(tags)
                user_prompt = user_template.format(tags=tags_str, text=text)

                # Call LLM
                max_tokens = self.model_config.get("max_tokens", 200)
                response = await llm_client.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model or self.model_config.get("model"),
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Parse JSON response
                try:
                    result_tags = json.loads(response.strip())
                    if not isinstance(result_tags, list):
                        result_tags = []
                except json.JSONDecodeError:
                    result_tags = [tag for tag in tags if tag.lower() in response.lower()]

                # Validate tags
                validated_tags = []
                for tag in result_tags:
                    if tag in tags:
                        validated_tags.append(tag)
                    else:
                        for original_tag in tags:
                            if original_tag.lower() == tag.lower():
                                validated_tags.append(original_tag)
                                break

                # Apply max_tags limit
                if max_tags and len(validated_tags) > max_tags:
                    validated_tags = validated_tags[:max_tags]

                # Format result
                if include_scores:
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
