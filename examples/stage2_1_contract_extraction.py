"""
Example: Contract Extraction with Complex Schema

Demonstrates Stage 2.1 features:
- Nested object support
- Type coercion (string → number, date parsing)
- Nullable fields
- Array handling
- Schema validation with retry logic
"""

import asyncio
from src.tools.extract_by_llm import extract_by_llm


# Example contract text
CONTRACT_TEXT = """
SERVICES AGREEMENT

This Services Agreement ("Agreement") is entered into as of December 15, 2025,
between TechCorp Inc. ("Client") and DataSystems LLC ("Vendor").

1. SERVICES
Vendor shall provide cloud infrastructure services as described in Exhibit A.

2. PAYMENT TERMS
- Setup Fee: $5,000 (one-time)
- Monthly Fee: $2,500
- Penalty for late payment: $250 per day

3. DELIVERY
Services shall commence on January 1, 2026.
Initial setup must be completed by January 15, 2026.

4. PARTIES
Client: TechCorp Inc., represented by Jane Smith (CEO)
Vendor: DataSystems LLC, represented by John Doe (VP Sales)

5. TERM
This agreement is valid for 12 months from the start date.
"""


# Define complex schema with nested objects and type constraints
CONTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "agreement_date": {
            "type": ["string", "null"],
            "format": "date",
            "description": "Date the agreement was signed"
        },
        "parties": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": ["string", "null"]},
                    "representative": {"type": ["string", "null"]}
                },
                "required": ["name"]
            },
            "description": "List of parties involved in the contract"
        },
        "financial_terms": {
            "type": "object",
            "properties": {
                "setup_fee": {"type": ["number", "null"]},
                "monthly_fee": {"type": ["number", "null"]},
                "late_payment_penalty": {"type": ["number", "null"]}
            },
            "description": "Financial terms of the agreement"
        },
        "delivery_date": {
            "type": ["string", "null"],
            "format": "date",
            "description": "Service delivery start date"
        },
        "setup_deadline": {
            "type": ["string", "null"],
            "format": "date",
            "description": "Setup completion deadline"
        },
        "duration_months": {
            "type": ["integer", "null"],
            "description": "Contract duration in months"
        }
    },
    "required": ["parties"]
}


async def test_contract_extraction():
    """Test contract extraction with complex nested schema."""

    print("=" * 70)
    print("Stage 2.1 Example: Contract Extraction with Complex Schema")
    print("=" * 70)
    print()

    # Example 1: Extract with structured output and type coercion
    print("Example 1: Full contract extraction")
    print("-" * 70)

    result = await extract_by_llm(
        input=[CONTRACT_TEXT],
        response_format=CONTRACT_SCHEMA,
        args={
            "prompt": "Extract all contract details. Convert amounts to numbers without currency symbols. Parse dates in YYYY-MM-DD format.",
            "enable_coercion": True,  # Enable type coercion
            "max_retries": 2          # Allow 2 retries if validation fails
        }
    )

    print(f"Result ID: {result[0]['id']}")
    print(f"Success: {'error' not in result[0]}")

    if 'result' in result[0] and result[0]['result']:
        extracted = result[0]['result']
        print(f"\nExtracted Data:")
        print(f"  Agreement Date: {extracted.get('agreement_date')}")
        print(f"  Delivery Date: {extracted.get('delivery_date')}")
        print(f"  Setup Deadline: {extracted.get('setup_deadline')}")
        print(f"  Duration: {extracted.get('duration_months')} months")
        print(f"\n  Financial Terms:")
        if 'financial_terms' in extracted:
            print(f"    Setup Fee: ${extracted['financial_terms'].get('setup_fee')}")
            print(f"    Monthly Fee: ${extracted['financial_terms'].get('monthly_fee')}")
            print(f"    Penalty: ${extracted['financial_terms'].get('late_payment_penalty')}/day")
        print(f"\n  Parties ({len(extracted.get('parties', []))}):")
        for party in extracted.get('parties', []):
            print(f"    - {party.get('name')}")
            if party.get('representative'):
                print(f"      Rep: {party.get('representative')}")

    if 'error' in result[0]:
        print(f"\nError: {result[0]['error']}")

    print()
    print("=" * 70)
    print()

    # Example 2: Simple field extraction
    print("Example 2: Simple field list extraction")
    print("-" * 70)

    result2 = await extract_by_llm(
        input=[CONTRACT_TEXT],
        fields=["agreement_date", "delivery_date", "duration_months"],
        args={
            "prompt": "Extract dates in YYYY-MM-DD format and duration as a number"
        }
    )

    print(f"Result ID: {result2[0]['id']}")
    if 'result' in result2[0]:
        print(f"Extracted: {result2[0]['result']}")

    print()
    print("=" * 70)

    # Example 3: Type coercion demonstration
    print("\nExample 3: Type Coercion Examples")
    print("-" * 70)

    from src.services.type_coercion import TypeCoercer

    print("Number coercion:")
    print(f"  '$5,000' → {TypeCoercer.coerce_to_number('$5,000')}")
    print(f"  '25%' → {TypeCoercer.coerce_to_number('25%')}")
    print(f"  '2,500.50' → {TypeCoercer.coerce_to_number('2,500.50')}")

    print("\nDate coercion:")
    print(f"  'December 15, 2025' → {TypeCoercer.coerce_to_date('December 15, 2025')}")
    print(f"  '01/15/2026' → {TypeCoercer.coerce_to_date('01/15/2026')}")
    print(f"  'Jan 1, 2026' → {TypeCoercer.coerce_to_date('Jan 1, 2026')}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    print("\n🚀 Running Stage 2.1 Contract Extraction Example\n")
    asyncio.run(test_contract_extraction())
    print("\n✅ Example completed!\n")
