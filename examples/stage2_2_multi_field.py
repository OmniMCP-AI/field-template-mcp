"""
Example: Multi-Field Classification and Extraction

Demonstrates Stage 2.2 features:
- Field reference system ({$field_name})
- Multiple input fields in prompts
- Dynamic prompt generation
- Context-aware classification
"""

import asyncio
from src.services.field_resolver import FieldResolver
from src.tools.classify_by_llm import classify_by_llm
from src.tools.extract_by_llm import extract_by_llm


# Example 1: Gender Classification with Multiple Fields
async def example_gender_classification():
    """
    Classify gender based on name and person description.
    Uses field references to combine multiple inputs.
    """
    print("=" * 70)
    print("Example 1: Gender Classification with Multi-Field Context")
    print("=" * 70)
    print()

    # Data with multiple fields per item
    people_data = [
        {"id": "p1", "data": {"name": "John Smith", "person": "software engineer at Google"}},
        {"id": "p2", "data": {"name": "Maria Garcia", "person": "doctor at city hospital"}},
        {"id": "p3", "data": {"name": "Alex Taylor", "person": "freelance designer"}},
    ]

    # Template with field references
    prompt_template = """Classify gender based on the following information:
Name: {$name}
Person: {$person}

Consider context clues from the description."""

    # Process each person
    results = []
    for person in people_data:
        # Extract fields from data
        inputs = person["data"]

        # Resolve field references in prompt
        resolved_prompt = FieldResolver.resolve(prompt_template, inputs)

        print(f"Person ID: {person['id']}")
        print(f"Resolved Prompt:\n{resolved_prompt}")
        print()

        # Note: In actual implementation, we'd call classify_by_llm with the resolved prompt
        # For demo, we're just showing the prompt resolution
        results.append({
            "id": person["id"],
            "resolved_prompt": resolved_prompt,
            "fields": inputs
        })

    print("-" * 70)
    print(f"Processed {len(results)} items with multi-field context")
    print()


# Example 2: Format Field with Type Parameter
async def example_format_field():
    """
    Format data based on field type parameter.
    Demonstrates dynamic behavior based on input fields.
    """
    print("=" * 70)
    print("Example 2: Format Field with Dynamic Type")
    print("=" * 70)
    print()

    # Data with format type specified
    format_requests = [
        {"input_data": "1234.56", "field_type": "currency"},
        {"input_data": "0.25", "field_type": "percentage"},
        {"input_data": "2025-10-17", "field_type": "date"},
        {"input_data": "1234567", "field_type": "number"},
    ]

    # Template with field references
    prompt_template = """Format the following data as {$field_type}:

Data: {$input_data}

Valid formats:
- currency: Add currency symbol and format with commas
- percentage: Convert to percentage format
- date: Format as human-readable date
- number: Format with thousands separators

Return only the formatted value."""

    for i, request in enumerate(format_requests):
        # Resolve prompt with both fields
        resolved = FieldResolver.resolve(prompt_template, request)

        print(f"Request {i+1}:")
        print(f"  Input: {request['input_data']}")
        print(f"  Type: {request['field_type']}")
        print(f"  Resolved Prompt (excerpt):")
        print(f"    \"Format...data as {request['field_type']}\"")
        print(f"    \"Data: {request['input_data']}\"")
        print()

    print("-" * 70)
    print()


# Example 3: Multi-Field Extraction
async def example_multi_field_extraction():
    """
    Extract information using multiple context fields.
    """
    print("=" * 70)
    print("Example 3: Multi-Field Context Extraction")
    print("=" * 70)
    print()

    # Data with context and target text
    extraction_tasks = [
        {
            "context": "Technical documentation",
            "source": "internal wiki",
            "text": "The API endpoint is /api/v1/users. Authentication requires Bearer token."
        },
        {
            "context": "Customer support ticket",
            "source": "email",
            "text": "Customer John Doe (john@example.com) reported issue #12345 on Oct 15."
        }
    ]

    # Template that uses context fields
    prompt_template = """Extract key information from the following text.

Context: {$context}
Source: {$source}

Text:
{$text}

Extract: endpoints, authentication_method (if technical) OR customer_name, issue_id (if support ticket)"""

    for i, task in enumerate(extraction_tasks):
        resolved = FieldResolver.resolve(prompt_template, task)

        print(f"Task {i+1}:")
        print(f"  Context: {task['context']}")
        print(f"  Source: {task['source']}")
        print(f"  Text (excerpt): {task['text'][:50]}...")
        print()

    print("-" * 70)
    print()


# Example 4: Field Reference Utilities
def example_field_utilities():
    """
    Demonstrate field resolver utility functions.
    """
    print("=" * 70)
    print("Example 4: Field Resolver Utilities")
    print("=" * 70)
    print()

    prompt = "Analyze {$input_text} based on {$category} and {$priority}"

    # Extract references
    refs = FieldResolver.extract_field_references(prompt)
    print(f"1. Extract Field References:")
    print(f"   Prompt: \"{prompt}\"")
    print(f"   Fields: {refs}")
    print()

    # Check if has references
    print(f"2. Check for References:")
    print(f"   Has references: {FieldResolver.has_field_references(prompt)}")
    print(f"   Simple prompt: {FieldResolver.has_field_references('No refs here')}")
    print()

    # Validate fields
    inputs = {"input_text": "Sample text", "category": "urgent"}
    valid, missing = FieldResolver.validate_fields(prompt, inputs)
    print(f"3. Validate Fields:")
    print(f"   Available: {list(inputs.keys())}")
    print(f"   Required: {refs}")
    print(f"   Valid: {valid}")
    print(f"   Missing: {missing}")
    print()

    # Resolve with defaults
    resolved = FieldResolver.resolve(prompt, inputs, default="[NOT PROVIDED]")
    print(f"4. Resolve with Defaults:")
    print(f"   Resolved: \"{resolved}\"")
    print()

    # Create context
    context = FieldResolver.create_field_context(inputs)
    print(f"5. Create Field Context:")
    print(f"   {context}")
    print()

    print("=" * 70)
    print()


# Example 5: Real-World Use Case - Product Classification
async def example_product_classification():
    """
    Classify products using multiple attributes.
    """
    print("=" * 70)
    print("Example 5: Product Classification with Multiple Attributes")
    print("=" * 70)
    print()

    products = [
        {
            "name": "iPhone 15 Pro",
            "description": "Latest smartphone with A17 chip",
            "price": "$999",
            "brand": "Apple"
        },
        {
            "name": "MacBook Air M3",
            "description": "Lightweight laptop with M3 processor",
            "price": "$1299",
            "brand": "Apple"
        },
        {
            "name": "AirPods Pro",
            "description": "Wireless earbuds with noise cancellation",
            "price": "$249",
            "brand": "Apple"
        }
    ]

    prompt_template = """Classify the product into a category based on:

Product: {$name}
Description: {$description}
Price: {$price}
Brand: {$brand}

Categories: smartphone, laptop, tablet, accessory, wearable"""

    print("Products to classify:")
    for i, product in enumerate(products, 1):
        resolved = FieldResolver.resolve(prompt_template, product)
        print(f"\n{i}. {product['name']}")
        print(f"   Fields: name={product['name']}, brand={product['brand']}, price={product['price']}")
        print(f"   Prompt resolved ✓")

    print()
    print("-" * 70)
    print()


async def main():
    """Run all Stage 2.2 examples."""
    print("\n🚀 Stage 2.2: Multi-Field Examples\n")

    await example_gender_classification()
    await example_format_field()
    await example_multi_field_extraction()
    example_field_utilities()
    await example_product_classification()

    print("✅ All Stage 2.2 examples completed!\n")


if __name__ == "__main__":
    asyncio.run(main())
