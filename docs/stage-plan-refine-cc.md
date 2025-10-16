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
│  • Lists available field templates as tools                      │
│  • Converts template config to MCP tool metadata                │
│  • Validates input against input_schema                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Execute template
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│            Template Service (template_service.py)                │
│  • Loads template from config                                    │
│  • Resolves field references {$field_name}                      │
│  • Assembles prompt with user inputs                            │
│  • Calls LLM with prompt and model config                       │
│  • Validates output against output_schema                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Return result
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AI Agent / User                               │
│  • Receives structured data                                      │
│  • Uses result in workflow                                       │
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

## Stage 1: Config-to-Tool Mechanism

**Goal:** Implement the core mechanism to read field template configs and dynamically generate MCP tools.

### Stage 1.0: Core Infrastructure

**Tasks:**
1. Create config directory structure
   ```
   configs/
   ├── templates/
   │   ├── classify/
   │   ├── tags/
   │   ├── extract/
   │   └── summarize/
   └── schema.json (template schema definition)
   ```

2. Define template configuration schema
   ```python
   class FieldTemplate(BaseModel):
       template_id: str
       name: str
       description: str
       category: str  # classify, extract, generate, analyze
       prompt_template: str
       input_schema: Dict[str, Any]  # JSON Schema
       output_schema: Dict[str, Any]  # JSON Schema
       model_config: ModelConfig
       field_references: List[str] = []  # {$field_name} patterns
   ```

3. Create template loader service
   ```python
   class TemplateRegistry:
       def load_templates(self, directory: str) -> List[FieldTemplate]
       def get_template(self, template_id: str) -> FieldTemplate
       def list_templates(self, category: str = None) -> List[FieldTemplate]
   ```

4. Implement dynamic tool generation
   ```python
   def create_mcp_tool_from_template(template: FieldTemplate):
       """Convert template to MCP tool with proper schemas"""
       # Generate function with input validation
       # Add to MCP server dynamically
   ```

**Deliverables:**
- `src/models/template.py` - Template data models
- `src/services/template_registry.py` - Template loading and management
- `src/services/template_executor.py` - Template execution logic
- `configs/schema.json` - Template schema definition

**Test Criteria:**
- Templates can be loaded from JSON files
- Templates are converted to MCP tools
- Tools appear in MCP `list_tools` response

---

### Stage 1.1: Basic Template Implementations

**Goal:** Implement 4 simple field templates with hardcoded prompts.

#### Template 1: `classify`
```json
{
  "template_id": "classify_simple",
  "name": "Simple Classification",
  "description": "Classify input data into categories",
  "category": "classify",
  "prompt_template": "Classify the following text into one of these categories: {categories}\n\nText: {input_data}\n\nReturn only the category name.",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_data": {"type": "string"},
      "categories": {"type": "string"}
    },
    "required": ["input_data", "categories"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "category": {"type": "string"}
    },
    "required": ["category"]
  },
  "model_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_tokens": 100
  }
}
```

#### Template 2: `tags`
```json
{
  "template_id": "tags_extract",
  "name": "Extract Tags",
  "description": "Extract relevant tags from input data",
  "category": "extract",
  "prompt_template": "Extract relevant tags from the following text. Return as a JSON array of strings.\n\nText: {input_data}\n\nTags:",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_data": {"type": "string"}
    },
    "required": ["input_data"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "tags": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "required": ["tags"]
  },
  "model_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 200
  }
}
```

#### Template 3: `extract_by_fields`
```json
{
  "template_id": "extract_fields",
  "name": "Extract by Fields",
  "description": "Extract specific fields from input data",
  "category": "extract",
  "prompt_template": "Extract the following fields from the text:\n\nFields to extract: {expected_fields}\n\nText: {input_data}\n\nReturn as JSON with the specified fields as keys.",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_data": {"type": "string"},
      "expected_fields": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "required": ["input_data", "expected_fields"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "data": {
        "type": "array",
        "items": {"type": "object"}
      }
    },
    "required": ["data"]
  },
  "model_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "max_tokens": 500
  }
}
```

#### Template 4: `summarize`
```json
{
  "template_id": "summarize_simple",
  "name": "Simple Summarization",
  "description": "Summarize input data concisely",
  "category": "summarize",
  "prompt_template": "Summarize the following text concisely:\n\n{input_data}\n\nSummary:",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_data": {"type": "string"}
    },
    "required": ["input_data"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "summary": {"type": "string"}
    },
    "required": ["summary"]
  },
  "model_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.5,
    "max_tokens": 300
  }
}
```

**Implementation Tasks:**
1. Create JSON files in `configs/templates/`
2. Implement `TemplateExecutor.execute(template_id, inputs)`
3. Add LLM client integration (OpenAI, Claude, etc.)
4. Parse and validate LLM output against `output_schema`

**Test Cases:**
```python
# Test classify
result = execute_template("classify_simple", {
    "input_data": "This is a great product!",
    "categories": "positive, negative, neutral"
})
assert result["category"] in ["positive", "negative", "neutral"]

# Test tags
result = execute_template("tags_extract", {
    "input_data": "Machine learning and AI are transforming technology"
})
assert isinstance(result["tags"], list)

# Test extract_by_fields
result = execute_template("extract_fields", {
    "input_data": "John Doe, age 30, lives in NYC",
    "expected_fields": ["name", "age", "city"]
})
assert "name" in result["data"][0]

# Test summarize
result = execute_template("summarize_simple", {
    "input_data": "Long text here..."
})
assert isinstance(result["summary"], str)
```

**Deliverables:**
- 4 template JSON files
- `src/services/llm_client.py` - LLM integration
- `src/services/output_validator.py` - Output schema validation
- `tests/test_stage1_1.py` - Test cases

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

## Stage 3: Template Management System

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

## Stage 4: Advanced Features

### Stage 4.1: AI-Powered Template Generation

**Goal:** Generate templates automatically from user descriptions.

**Flow:**
```
User: "I want to extract product information from descriptions"
  ↓
AI analyzes requirements
  ↓
Generates template with:
  - Appropriate prompt
  - Input schema
  - Output schema
  - Field definitions
  ↓
User reviews and confirms
  ↓
Template saved and registered
```

**Implementation:**
```python
async def generate_template_from_description(
    description: str,
    sample_input: str = None,
    expected_output_format: str = None
) -> FieldTemplate:
    """
    Use LLM to generate template configuration
    """
    prompt = f"""
    Generate a field template configuration for:
    {description}

    Sample input: {sample_input}
    Expected output: {expected_output_format}

    Return JSON with: prompt_template, input_schema, output_schema
    """
    # ... implementation
```

**Tasks:**
- Implement template generation prompt
- Add sample testing during generation
- Support iterative refinement
- Validate generated templates

---

### Stage 4.2: Batch Processing

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

### Stage 4.3: Template Chaining

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

### Stage 4.4: Caching and Optimization

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

## Stage 5: Production Readiness

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
