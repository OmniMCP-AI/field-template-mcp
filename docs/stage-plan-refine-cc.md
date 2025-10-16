# Field Template MCP - Staged Implementation Plan

## Overview

This document outlines a comprehensive staged implementation plan for building an **AI Field Template System** using the **MCP (Model Context Protocol)**. The system enables users to create configurable, reusable field templates that automatically process and transform data using LLMs.

### Core Concept

**Template Configuration → MCP Tools → LLM Processing → Structured Output**

Similar to how the scraper plugin converts scraping templates into MCP tools, this system converts field templates (with prompts and schemas) into callable MCP tools that agents can use for data classification, extraction, generation, and transformation.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Agent / Claude Desktop                     │
│                     (via MCP Interface)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ 1. List Tools (GET)
                            │ 2. Call Tool (POST)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server (main.py)                          │
│  • Registers 3 core tools:                                       │
│    - classify_by_llm                                            │
│    - tag_by_llm                                                 │
│    - extract_by_llm                                             │
│  • Validates input against schemas                              │
│  • Normalizes input format                                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Execute tool
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│               Tool Handlers (src/tools/)                         │
│  • classify_by_llm_handler.py                                   │
│  • tag_by_llm_handler.py                                        │
│  • extract_by_llm_handler.py                                    │
│                                                                  │
│  Each handler:                                                   │
│  • Normalizes input to {id, data} format                        │
│  • Batch processes all items                                    │
│  • Calls LLM via LLMClient                                      │
│  • Returns {id, result, error} format                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ LLM API calls
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   LLM Client (llm_client.py)                     │
│  • Provider abstraction (OpenAI, Anthropic, etc.)               │
│  • Structured output support (JSON Schema)                      │
│  • Error handling and retries                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Return results
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AI Agent / User                               │
│  • Receives batch results with IDs                              │
│  • Each result: {id, result, error?}                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage 0: Project Initialization ✅

**Goal:** Set up basic MCP server with SSE transport and verify tool discovery works.

**Status:** COMPLETED (based on existing code)

### Tasks Completed:
- ✅ Initialize FastMCP server with SSE transport
- ✅ Basic `/sse` endpoint for MCP communication
- ✅ Simple health check tool (`example_tool`)
- ✅ Test via MCP inspector or Claude Desktop

### Current State:
```python
# main.py
mcp = FastMCP("AI Field Template MCP Server")

@mcp.tool()
def example_tool(name: str) -> str:
    return f"Hello {name}"
```

### Verification:
- Run: `python main.py`
- Access: `http://localhost:8000/sse`
- Tools should be discoverable

---

## Stage 1: Core MCP Tools Implementation

**Goal:** Implement the 3 core MCP tools directly (no config files) following SPECIFICATION.md API design.

### Stage 1.0: Core Infrastructure

**Tasks:**
1. Set up project structure
   ```
   src/
   ├── tools/              # MCP tool implementations
   ├── services/           # Business logic services
   │   ├── llm_client.py
   │   ├── input_normalizer.py
   │   └── batch_processor.py
   ├── models/             # Data models
   └── utils/              # Helper utilities
   tests/
   └── tools/              # Tool-specific tests
   ```

2. Define core data models
   ```python
   class InputItem(BaseModel):
       id: Union[int, str]
       data: Union[str, int, float, dict, bool, None]

   class OutputItem(BaseModel):
       id: Union[int, str]
       result: Any
       error: Optional[str] = None

   class BatchProcessResult(BaseModel):
       results: List[OutputItem]
       metadata: ProcessMetadata
   ```

3. Implement input normalization service
   ```python
   class InputNormalizer:
       @staticmethod
       def normalize(input: list) -> list[InputItem]:
           """Convert simple list to {id, data} format"""
           # ["text1", "text2"] → [{"id": 0, "data": "text1"}, ...]
   ```

4. Implement LLM client abstraction
   ```python
   class LLMClient:
       async def chat(self, messages: list, model: str, **kwargs) -> str
       async def structured_output(self, messages: list, schema: dict, model: str) -> dict
   ```

5. Register tools with FastMCP
   ```python
   @mcp.tool()
   async def classify_by_llm(
       input: list,
       categories: list[str],
       prompt: str = None,
       args: dict = None
   ) -> list[dict]:
       # Implementation
   ```

**Deliverables:**
- `src/models/base.py` - Core data models
- `src/services/llm_client.py` - LLM provider abstraction
- `src/services/input_normalizer.py` - Input normalization
- `src/services/batch_processor.py` - Batch processing
- `main.py` - Updated with tool registrations

**Test Criteria:**
- Tools are registered with FastMCP
- Tools appear in MCP `list_tools` response
- Input normalization works for both formats
- LLM client can connect to provider

---

### Stage 1.1: Basic MCP Tool Implementations

**Goal:** Implement 3 core MCP tools following the SPECIFICATION.md API design with batch processing.

**Key Design Principles from SPECIFICATION.md:**
- ✅ **Batch-first**: All operations process lists (not single items)
- ✅ **ID tracking**: Input/output uses `{id, data/result}` format
- ✅ **Consistent interface**: Uniform signature pattern across all operations
- ✅ **Type flexibility**: Support heterogeneous input types

---

#### Tool 1: `classify_by_llm`

**MCP Tool Name:** `classify_by_llm`

**Description:** Classify each input into exactly ONE best-matching category from predefined options using LLM.

**API Signature:**
```python
classify_by_llm(
    input: list[dict | str | int | float],
    categories: list[str],
    prompt: str | None = None,
    args: dict | None = None
) -> list[dict]
```

**Input Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "input": {
      "type": "array",
      "description": "List of items to classify. Each item can be a string, number, or dict with {id, data} format",
      "items": {
        "oneOf": [
          {"type": "string"},
          {"type": "number"},
          {"type": "object"}
        ]
      }
    },
    "categories": {
      "type": "array",
      "description": "List of possible categories (mutually exclusive)",
      "items": {"type": "string"},
      "minItems": 2
    },
    "prompt": {
      "type": "string",
      "description": "Optional instructions for classification context"
    },
    "args": {
      "type": "object",
      "properties": {
        "model": {"type": "string", "default": "claude-3-5-sonnet"},
        "temperature": {"type": "number", "default": 0},
        "include_scores": {"type": "boolean", "default": false},
        "allow_none": {"type": "boolean", "default": false}
      }
    }
  },
  "required": ["input", "categories"]
}
```

**Output Schema:**
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {"type": ["integer", "string"]},
      "result": {"type": ["string", "object", "null"]},
      "error": {"type": "string"}
    },
    "required": ["id"]
  }
}
```

---

#### Tool 2: `tag_by_llm`

**MCP Tool Name:** `tag_by_llm`

**Description:** Apply multiple relevant tags from a predefined set to each input (non-mutually exclusive).

**API Signature:**
```python
tag_by_llm(
    input: list[dict | str | int | float],
    tags: list[str],
    prompt: str | None = None,
    args: dict | None = None
) -> list[dict]
```

**Input Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "input": {
      "type": "array",
      "description": "List of items to tag",
      "items": {
        "oneOf": [
          {"type": "string"},
          {"type": "number"},
          {"type": "object"}
        ]
      }
    },
    "tags": {
      "type": "array",
      "description": "List of possible tags (can return 0-N tags per item)",
      "items": {"type": "string"},
      "minItems": 1
    },
    "prompt": {
      "type": "string",
      "description": "Optional instructions for tagging context"
    },
    "args": {
      "type": "object",
      "properties": {
        "model": {"type": "string", "default": "claude-3-5-sonnet"},
        "temperature": {"type": "number", "default": 0},
        "max_tags": {"type": "integer", "description": "Maximum tags per item"},
        "include_scores": {"type": "boolean", "default": false}
      }
    }
  },
  "required": ["input", "tags"]
}
```

**Output Schema:**
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {"type": ["integer", "string"]},
      "result": {
        "type": "array",
        "items": {
          "oneOf": [
            {"type": "string"},
            {
              "type": "object",
              "properties": {
                "tag": {"type": "string"},
                "score": {"type": "number"}
              }
            }
          ]
        }
      },
      "error": {"type": "string"}
    },
    "required": ["id", "result"]
  }
}
```

---

#### Tool 3: `extract_by_llm`

**MCP Tool Name:** `extract_by_llm`

**Description:** Extract specific fields from unstructured text using LLM semantic understanding.

**API Signature:**
```python
extract_by_llm(
    input: list[dict | str | int | float],
    fields: list[str] | None = None,
    response_format: dict | None = None,
    args: dict | None = None
) -> list[dict]
```

**Input Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "input": {
      "type": "array",
      "description": "List of items to extract from",
      "items": {
        "oneOf": [
          {"type": "string"},
          {"type": "number"},
          {"type": "object"}
        ]
      }
    },
    "fields": {
      "type": "array",
      "description": "List of field names to extract (required if response_format not provided)",
      "items": {"type": "string"}
    },
    "response_format": {
      "type": "object",
      "description": "JSON Schema for structured output (OpenAI-compatible)"
    },
    "args": {
      "type": "object",
      "properties": {
        "model": {"type": "string", "default": "claude-3-5-sonnet"},
        "temperature": {"type": "number", "default": 0},
        "max_tokens": {"type": "integer", "default": 1000},
        "prompt": {"type": "string", "description": "Custom extraction instructions"}
      }
    }
  },
  "required": ["input"],
  "oneOf": [
    {"required": ["fields"]},
    {"required": ["response_format"]}
  ]
}
```

**Output Schema:**
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {"type": ["integer", "string"]},
      "result": {"type": ["object", "null"]},
      "error": {"type": "string"}
    },
    "required": ["id"]
  }
}
```

---

**Implementation Tasks:**

1. **Implement core MCP tool handlers** in `src/tools/`

Each tool follows this pattern:

```python
# src/tools/classify_by_llm.py

from fastmcp import FastMCP

@mcp.tool()
async def classify_by_llm(
    input: list,
    categories: list[str],
    prompt: str = None,
    args: dict = None
) -> list[dict]:
    """
    Classify each input into exactly ONE best-matching category.

    Args:
        input: List of items to classify (strings, numbers, or dicts with {id, data})
        categories: List of possible categories (mutually exclusive)
        prompt: Optional custom instructions for classification context
        args: Optional config (model, temperature, include_scores, etc.)

    Returns:
        List of {id, result, error?} dicts

    Example:
        result = await classify_by_llm(
            input=["Apple releases new iPhone", "Lakers win game"],
            categories=["tech", "sports", "politics"]
        )
        # → [{"id": 0, "result": "tech"}, {"id": 1, "result": "sports"}]
    """
    # 1. Normalize input to {id, data} format
    normalized = InputNormalizer.normalize(input)

    # 2. Extract config from args
    model = args.get("model", "claude-3-5-sonnet") if args else "claude-3-5-sonnet"
    include_scores = args.get("include_scores", False) if args else False

    # 3. Build prompt
    system_prompt = "You are a classification expert. Classify text into exactly ONE category."
    if prompt:
        system_prompt += f"\n\n{prompt}"

    # 4. Process batch with error handling
    results = []
    for item in normalized:
        try:
            user_prompt = f"Categories: {', '.join(categories)}\n\nText: {item['data']}"

            # Call LLM
            response = await llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model
            )

            # Parse result
            category = response.strip()

            if include_scores:
                result = {"category": category, "score": 0.95}  # Mock score
            else:
                result = category

            results.append({"id": item["id"], "result": result})

        except Exception as e:
            results.append({"id": item["id"], "result": None, "error": str(e)})

    return results
```

2. **Implement input normalization service**

```python
# src/services/input_normalizer.py

class InputNormalizer:
    @staticmethod
    def normalize(input: list) -> list[dict]:
        """
        Convert various input formats to standard {id, data} format.

        Examples:
            ["text1", "text2"] → [{"id": 0, "data": "text1"}, {"id": 1, "data": "text2"}]
            [{"id": "custom", "data": "text"}] → [{"id": "custom", "data": "text"}]
        """
        if not isinstance(input, list):
            raise TypeError("Input must be a list")

        normalized = []
        auto_id_counter = 0

        for item in input:
            # Already in {id, data} format
            if isinstance(item, dict) and "id" in item and "data" in item:
                normalized.append(item)

            # Dict without proper format
            elif isinstance(item, dict):
                # If has id but no data, treat whole dict as data
                if "id" in item:
                    normalized.append({"id": item["id"], "data": item})
                else:
                    # No id, assign auto id
                    normalized.append({"id": auto_id_counter, "data": item})
                    auto_id_counter += 1

            # Simple value (string, number, bool, None)
            else:
                normalized.append({"id": auto_id_counter, "data": item})
                auto_id_counter += 1

        return normalized
```

3. **Implement LLM client with provider abstraction**

```python
# src/services/llm_client.py

class LLMClient:
    def __init__(self, provider: str = "anthropic"):
        self.provider = provider
        if provider == "anthropic":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def chat(
        self,
        messages: list[dict],
        model: str = "claude-3-5-sonnet",
        temperature: float = 0,
        max_tokens: int = 1000
    ) -> str:
        """Send chat request to LLM and return response."""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text

        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

    async def structured_output(
        self,
        messages: list[dict],
        schema: dict,
        model: str = "claude-3-5-sonnet"
    ) -> dict:
        """Get structured JSON output from LLM."""
        # For Anthropic: Use tool use pattern
        # For OpenAI: Use response_format parameter
        pass
```

4. **Add batch processing logic** (Optional for now, can process sequentially first)

```python
# src/services/batch_processor.py

import asyncio

async def batch_process(
    items: list[dict],
    operation: callable,
    max_concurrent: int = 5
) -> list[dict]:
    """
    Process items in parallel with concurrency limit.

    Args:
        items: List of normalized items {id, data}
        operation: Async function to process each item
        max_concurrent: Max concurrent operations

    Returns:
        List of results maintaining input order
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(item):
        async with semaphore:
            try:
                result = await operation(item)
                return {"id": item["id"], "result": result}
            except Exception as e:
                return {"id": item["id"], "result": None, "error": str(e)}

    # Process all items concurrently (up to max_concurrent)
    tasks = [process_with_semaphore(item) for item in items]
    results = await asyncio.gather(*tasks)

    return results
```

5. **Implement output validation** (Optional for Stage 1.1, required for Stage 1.2)

```python
# src/services/output_validator.py

import jsonschema

def validate_output(result: any, schema: dict) -> bool:
    """Validate result against JSON Schema."""
    try:
        jsonschema.validate(instance=result, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"Output validation failed: {e.message}")
```

---

**Test Cases (Following SPECIFICATION.md examples):**

```python
# Test 1: classify_by_llm - Basic classification
result = await classify_by_llm(
    input=[
        {"id": 0, "data": "What to know about Trump's $20B bailout for Argentina"},
        {"id": 1, "data": "Lakers win championship"}
    ],
    categories=["entertainment", "economy", "policy", "sports"]
)
assert result == [
    {"id": 0, "result": "economy"},
    {"id": 1, "result": "sports"}
]

# Test 2: classify_by_llm - Simple list input (auto-assigned IDs)
result = await classify_by_llm(
    input=["Apple releases new iPhone", "Lakers win game"],
    categories=["tech", "sports", "politics"]
)
assert result == [
    {"id": 0, "result": "tech"},
    {"id": 1, "result": "sports"}
]

# Test 3: classify_by_llm - With custom prompt and scores
result = await classify_by_llm(
    input=["This startup raised $50M for AI product"],
    categories=["tech", "business", "finance"],
    prompt="Focus on the main action or event",
    args={"include_scores": True}
)
assert result[0]["result"]["category"] in ["tech", "business", "finance"]
assert "score" in result[0]["result"]

# Test 4: tag_by_llm - Multiple tags returned
result = await tag_by_llm(
    input=[{"id": 0, "data": "Building a REST API with Python and PostgreSQL"}],
    tags=["AI", "backend", "frontend", "database", "operations"]
)
assert result == [
    {"id": 0, "result": ["backend", "database"]}
]

# Test 5: tag_by_llm - Simple list with custom prompt
result = await tag_by_llm(
    input=["Python REST API", "React frontend app"],
    tags=["python", "javascript", "database", "backend", "frontend"],
    prompt="Tag based on main technologies"
)
assert result == [
    {"id": 0, "result": ["python", "backend"]},
    {"id": 1, "result": ["javascript", "frontend"]}
]

# Test 6: tag_by_llm - No matching tags (empty result)
result = await tag_by_llm(
    input=["Generic unrelated content"],
    tags=["AI", "backend", "frontend"]
)
assert result == [{"id": 0, "result": []}]

# Test 7: extract_by_llm - Multi-field extraction
result = await extract_by_llm(
    input=[
        "Article text about AI... by Wade on 2025-10-12",
        "Tech news story... by Jones on 2025-10-13"
    ],
    fields=["title", "author", "date"]
)
assert result[0]["result"] == {"title": "...", "author": "Wade", "date": "2025-10-12"}
assert result[1]["result"] == {"title": "...", "author": "Jones", "date": "2025-10-13"}

# Test 8: extract_by_llm - Single field (still returns dict)
result = await extract_by_llm(
    input=["Long article... nvidia hit all time high... by Wade..."],
    fields=["title"]
)
assert result == [{"id": 0, "result": {"title": "nvidia hit all time high"}}]

# Test 9: extract_by_llm - With response_format (structured output)
result = await extract_by_llm(
    input=["Article with multiple authors: Wade, Smith. Tags: AI, tech"],
    response_format={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "authors": {
                "type": "array",
                "items": {"type": "string"}
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["title", "authors"]
    }
)
assert result[0]["result"]["authors"] == ["Wade", "Smith"]
assert result[0]["result"]["tags"] == ["AI", "tech"]

# Test 10: Error handling - Failed items
result = await classify_by_llm(
    input=["Valid content", "Invalid content", "Another valid"],
    categories=["tech", "sports"]
)
# Should have error marker for failed item
assert any("error" in item for item in result if item["id"] == 1)
assert result[0]["result"] is not None
assert result[2]["result"] is not None

# Test 11: Batch processing - Large list
result = await tag_by_llm(
    input=[f"Article {i} about tech" for i in range(100)],
    tags=["tech", "business", "sports"]
)
assert len(result) == 100
assert all("id" in item for item in result)
```

**Deliverables:**
- `src/tools/classify_by_llm.py` - Classification tool
- `src/tools/tag_by_llm.py` - Tagging tool
- `src/tools/extract_by_llm.py` - Extraction tool
- `src/services/llm_client.py` - LLM provider abstraction
- `src/services/input_normalizer.py` - Input format normalization
- `src/services/batch_processor.py` - Batch processing logic
- `tests/test_classify_by_llm.py` - Classification tests
- `tests/test_tag_by_llm.py` - Tagging tests
- `tests/test_extract_by_llm.py` - Extraction tests

---

### Stage 1.2: MCP Protocol Compliance

**Goal:** Verify that templates follow MCP protocol standards and match reference implementations.

**Tasks:**
1. Compare generated tools with `docs/reference-template.json`
2. Ensure input schemas use JSON Schema Draft 7
3. Validate output schemas are properly structured
4. Add tool descriptions in MCP format:
   ```
   - <description> What the tool does
   - <use_case> When to use it
   - <limitation> What it cannot do
   - <failure_cases> When it might fail
   ```

5. Implement error handling and status codes
6. Add metadata to tool responses

**Compliance Checklist:**
- [ ] Input schemas follow JSON Schema Draft 7
- [ ] Output schemas properly structured
- [ ] Tool names follow camelCase convention
- [ ] Descriptions include all sections
- [ ] Error responses include proper status codes
- [ ] Required vs optional fields properly marked

**Deliverables:**
- Updated template schemas
- `docs/mcp_compliance_report.md`
- `tests/test_mcp_compliance.py`

---

## Stage 2: Advanced Schema Support

**Goal:** Handle complex output schemas with nested objects and type validation.

### Stage 2.1: Complex JSON Output

**Tasks:**
1. Implement nested object support in output schemas
   ```json
   {
     "output_schema": {
       "type": "object",
       "properties": {
         "data": {
           "type": "array",
           "items": {
             "type": "object",
             "properties": {
               "name": {"type": "string"},
               "details": {
                 "type": "object",
                 "properties": {
                   "age": {"type": "number"},
                   "email": {"type": "string"}
                 }
               }
             }
           }
         }
       }
     }
   }
   ```

2. Add type coercion and validation
   - String → Number conversion
   - String → Date parsing
   - Enum validation
   - Nullable fields support: `["string", "null"]`

3. Implement retry logic for invalid outputs
   - Parse LLM response
   - Validate against schema
   - If invalid, retry with error feedback

**Example Template: Contract Extraction**
```json
{
  "template_id": "extract_contract",
  "name": "Contract Information Extraction",
  "prompt_template": "Extract contract details from:\n{contract_text}\n\nReturn as JSON with: penalty_amount (number), delivery_date (date), parties (array)",
  "output_schema": {
    "type": "object",
    "properties": {
      "penalty_amount": {"type": ["number", "null"]},
      "delivery_date": {"type": ["string", "null"], "format": "date"},
      "parties": {
        "type": "array",
        "items": {"type": "string"}
      }
    }
  }
}
```

**Deliverables:**
- `src/services/schema_validator.py` - Advanced validation
- `src/services/type_coercion.py` - Type conversion
- Complex template examples
- `tests/test_stage2_1.py`

---

### Stage 2.2: Multiple Input Fields

**Goal:** Support templates that reference multiple input fields.

**Field Reference System:**
Users can reference other fields using `{$field_name}` syntax in prompts.

**Example:**
```json
{
  "template_id": "classify_gender",
  "prompt_template": "Classify gender based on:\nName: {$name}\nPerson: {$person}\n\nReturn: male, female, or unknown",
  "input_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "person": {"type": "string"}
    },
    "required": ["name"]
  },
  "field_references": ["name", "person"]
}
```

**Tasks:**
1. Implement field reference parser
   ```python
   def extract_field_references(prompt: str) -> List[str]:
       """Extract {$field_name} patterns from prompt"""
       return re.findall(r'\{\$(\w+)\}', prompt)
   ```

2. Add field resolution at runtime
   ```python
   def resolve_field_references(prompt: str, inputs: Dict) -> str:
       """Replace {$field_name} with actual values"""
       for field in field_references:
           prompt = prompt.replace(f"{{${field}}}", inputs.get(field, ""))
       return prompt
   ```

3. Support dynamic input schemas based on references

**Format Field Type Example:**
```json
{
  "template_id": "format_field",
  "prompt_template": "Format {$input_data} as {field_type}.\n\nValid types: number, currency, percentage, date",
  "input_schema": {
    "properties": {
      "input_data": {"type": "string"},
      "field_type": {
        "type": "string",
        "enum": ["number", "currency", "percentage", "date"]
      }
    }
  }
}
```

**Deliverables:**
- `src/services/field_resolver.py` - Field reference system
- Multi-input template examples
- Format field templates
- `tests/test_stage2_2.py`

---

---

### Stage 4.2: Batch Processing(future)

**Goal:** Process multiple data items in a single call.

**Example:**
```python
result = execute_template("classify_simple", {
    "batch": True,
    "items": [
        {"input_data": "Great product!", "categories": "positive,negative,neutral"},
        {"input_data": "Terrible quality", "categories": "positive,negative,neutral"},
        {"input_data": "It's okay", "categories": "positive,negative,neutral"}
    ]
})
# Returns: [
#   {"category": "positive"},
#   {"category": "negative"},
#   {"category": "neutral"}
# ]
```

**Tasks:**
- Add batch support to executor
- Implement parallel processing
- Add progress tracking
- Handle partial failures

---

### Stage 4.3: Template Chaining (future)

**Goal:** Chain multiple templates together.

**Example:**
```json
{
  "template_id": "analyze_and_summarize",
  "chain": [
    {
      "template_id": "extract_fields",
      "inputs": {
        "input_data": "{$input}",
        "expected_fields": ["title", "body", "author"]
      }
    },
    {
      "template_id": "classify_simple",
      "inputs": {
        "input_data": "{$previous.body}",
        "categories": "tech, business, entertainment"
      }
    },
    {
      "template_id": "summarize_simple",
      "inputs": {
        "input_data": "{$previous.body}"
      }
    }
  ]
}
```

**Tasks:**
- Implement chain executor
- Support referencing previous results
- Add error handling for chains
- Optimize for performance

---

### Stage 4.4: Caching and Optimization (future)

**Goal:** Cache results and optimize performance.

**Features:**
1. **Result Caching**
   - Cache identical inputs → outputs
   - TTL-based cache expiration
   - Redis or in-memory cache

2. **Prompt Optimization**
   - Track prompt performance
   - A/B test different prompts
   - Auto-optimize based on validation failures

3. **Model Selection**
   - Use cheaper models for simple tasks
   - Fallback to better models on failure
   - Cost tracking per template

**Implementation:**
```python
class TemplateCache:
    def get_cached_result(self, template_id: str, inputs: Dict) -> Optional[Dict]
    def cache_result(self, template_id: str, inputs: Dict, result: Dict, ttl: int)
    def invalidate_cache(self, template_id: str)
```

---

## Stage 5: Production Readiness (future)

### Tasks:

1. **Error Handling**
   - Comprehensive error types
   - Retry logic with exponential backoff
   - Graceful degradation

2. **Logging and Monitoring**
   - Request/response logging
   - Performance metrics
   - Error tracking
   - Usage analytics

3. **Rate Limiting**
   - Per-user rate limits
   - Per-template rate limits
   - Cost limits

4. **Security**
   - Input validation and sanitization
   - Output validation
   - API authentication
   - Secret management for API keys

5. **Documentation**
   - User guide
   - API reference
   - Template creation guide
   - Best practices

6. **Testing**
   - Unit tests (90%+ coverage)
   - Integration tests
   - Load tests
   - End-to-end tests

---


## Stage 7: Template Management System (very far furture)

**Goal:** Build a complete template management system with CRUD operations.

### Tasks:

1. **Template Storage**
   - Store templates in JSON files OR database
   - Support versioning
   - Track template usage statistics

2. **Template CRUD API**
   ```python
   # List templates
   GET /templates
   GET /templates/{category}

   # Get template
   GET /templates/{template_id}

   # Create template
   POST /templates

   # Update template
   PUT /templates/{template_id}

   # Delete template
   DELETE /templates/{template_id}

   # Execute template
   POST /templates/{template_id}/execute
   ```

3. **Template Metadata Enhancement**
   ```python
   class FieldTemplate(BaseModel):
       # ... existing fields ...
       created_at: datetime
       updated_at: datetime
       version: str
       author: str
       tags: List[str]
       examples: List[Dict]
       usage_count: int
   ```

4. **Template Validation**
   - Validate prompt syntax
   - Check field references exist in input_schema
   - Validate schemas are valid JSON Schema
   - Test template with sample data

**Deliverables:**
- `src/api/template_api.py` - REST API
- `src/services/template_manager.py` - Template management
- `docs/api_spec.md` - API documentation
- `tests/test_stage3.py`


---

## Implementation Principles

### 1. Don't Break the System
- Run tests after each stage
- Use feature flags for new features
- Maintain backward compatibility
- Rollback plan for each stage

### 2. Simple to Complex
- Start with basic templates
- Add complexity incrementally
- Validate at each step
- Get user feedback early

### 3. Test-Driven Development
- Write tests before implementation
- Test each template independently
- Integration tests for workflows
- Performance benchmarks

### 4. Documentation First
- Document APIs before coding
- Keep README updated
- Add inline comments
- Maintain changelog

---

## Success Criteria

### Stage 1
- [ ] 4 basic templates working
- [ ] Templates callable via MCP
- [ ] Input/output validation working
- [ ] Test coverage > 80%

### Stage 2
- [ ] Complex JSON schemas supported
- [ ] Multi-field input working
- [ ] Type coercion implemented
- [ ] Format fields working

### Stage 3
- [ ] Template CRUD API complete
- [ ] Storage system working
- [ ] Version control implemented
- [ ] Usage tracking active

### Stage 4
- [ ] AI template generation working
- [ ] Batch processing implemented
- [ ] Caching system active
- [ ] Performance optimized

### Stage 5
- [ ] Production deployment ready
- [ ] Monitoring dashboards live
- [ ] Documentation complete
- [ ] User onboarding smooth

---

## Timeline Estimate

| Stage | Duration | Dependencies |
|-------|----------|--------------|
| Stage 0 | ✅ Complete | None |
| Stage 1.0 | 2-3 days | Stage 0 |
| Stage 1.1 | 3-4 days | Stage 1.0 |
| Stage 1.2 | 1-2 days | Stage 1.1 |
| Stage 2.1 | 2-3 days | Stage 1.2 |
| Stage 2.2 | 2-3 days | Stage 2.1 |
| Stage 3 | 4-5 days | Stage 2.2 |
| Stage 4 | 5-7 days | Stage 3 |
| Stage 5 | 3-5 days | Stage 4 |
| **Total** | **~25-35 days** | |

---

## Technology Stack

### Core:
- **MCP Server:** FastMCP (Python)
- **LLM Clients:** OpenAI, Anthropic, etc.
- **Config Storage:** JSON files / MongoDB
- **Cache:** Redis (optional)
- **Validation:** jsonschema, pydantic

### Testing:
- **Unit Tests:** pytest
- **Integration:** pytest + MCP inspector
- **Load Testing:** locust

### Deployment:
- **Container:** Docker
- **Orchestration:** Docker Compose / Kubernetes
- **Monitoring:** Prometheus + Grafana

---

## Next Steps

1. **Review this plan** - Get feedback and approval
2. **Set up development environment** - Install dependencies
3. **Create project structure** - Folders, configs, tests
4. **Start Stage 1.0** - Build core infrastructure
5. **Iterate and refine** - Adjust based on learnings

---

## References

- Original requirement: `docs/mcp.md`
- Business features: `docs/dingding-ai-field-template.md`
- Product spec: `docs/requirement_field_template_simple_spec.md`
- MCP implementation: `docs/scraper-plugin-mcp-mechanism.md`
- Reference template: `docs/reference-template.json`

---

## Questions for Confirmation

1. **Storage:** JSON files vs MongoDB for templates?
2. **LLM Provider:** OpenAI, Anthropic, or multi-provider?
3. **Execution:** Synchronous or async (with queue like scraper)?
4. **Deployment:** Single server or distributed?
5. **UI:** Will there be a web UI for template management?

---

**Document Version:** 1.0
**Last Updated:** 2025-10-17
**Status:** Ready for Review

### for test case if @pytest is not easy to config and make it run sucessful , you could change to other method