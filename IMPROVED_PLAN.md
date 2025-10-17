# Improved Plan: Dynamic Config-Driven LLM Tool System

## Insights from fastestai-data/src/plugin

### Key Learnings:
1. **Pydantic Models** - Strong typing with `BaseModel` for configs
2. **Template-based architecture** - Templates stored in DB, converted to MCP tools
3. **Schema generation** - Input/output schemas generated dynamically
4. **No if-elif chains** - Generic execution based on template metadata

---

## Improved Architecture

### 1. **Replace JSON with Pydantic Models**

**Current:** JSON files in `configs/tools/`
**Improved:** Pydantic models with validation

```python
# src/tools/models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from enum import Enum

class OperationType(str, Enum):
    """Operation types for LLM tools"""
    SINGLE_CHOICE = "single_choice"      # classify
    MULTI_LABEL = "multi_label"          # tag
    EXTRACTION = "extraction"            # extract
    # Easy to add: RANKING, SCORING, COMPARISON, etc.

class PromptTemplates(BaseModel):
    """Prompt templates with variable placeholders"""
    system: str
    user: str
    structured_system: Optional[str] = None

class ModelConfig(BaseModel):
    """LLM model configuration"""
    provider: str = "openai"
    model: str = "openai/gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 1000

class ParameterDef(BaseModel):
    """Parameter definition for tool"""
    type: str
    description: str
    required: bool = False
    items: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None
    default: Optional[Any] = None

class LLMToolTemplate(BaseModel):
    """
    Universal LLM tool template.
    Based on ScraperTemplate from fastestai-data.
    """
    tool_name: str
    operation_type: OperationType  # 👈 Key field - determines execution strategy
    description: str
    category: Optional[str] = None
    version: str = "1.0.0"

    model_config: ModelConfig
    prompt_templates: PromptTemplates

    # Input parameters (like ActionInputParam in reference)
    parameters: Dict[str, ParameterDef]

    # Output schema (like output_template in reference)
    output_format: Dict[str, Any]

    # Examples for documentation
    examples: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
```

### 2. **Operation Strategy Pattern (No if-elif!)**

```python
# src/tools/operations/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class OperationStrategy(ABC):
    """Base class for operation strategies"""

    @abstractmethod
    async def execute(
        self,
        llm_client: LLMClient,
        template: LLMToolTemplate,
        normalized_input: List[Dict[str, Any]],
        **params
    ) -> List[Dict[str, Any]]:
        """Execute the operation"""
        pass

    def validate_params(self, template: LLMToolTemplate, params: Dict[str, Any]):
        """Validate required parameters for this operation"""
        pass


# src/tools/operations/single_choice.py
class SingleChoiceOperation(OperationStrategy):
    """
    Handles single-choice operations (classify).
    Works for ANY tool with operation_type="single_choice".
    """

    async def execute(self, llm_client, template, normalized_input, **params):
        # Get the list of choices (could be "categories", "options", "labels", etc.)
        choices_param = self._find_choices_param(template)
        choices = params.get(choices_param, [])

        if not choices or len(choices) < 2:
            raise ValueError(f"{choices_param} must have at least 2 items")

        results = []
        for item in normalized_input:
            # Use template's prompts
            system_prompt = template.prompt_templates.system
            user_prompt = template.prompt_templates.user.format(
                **{choices_param: ", ".join(choices), "text": item["data"]}
            )

            # Add custom prompt if provided
            if params.get("prompt"):
                system_prompt += f"\n\n{params['prompt']}"

            response = await llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=params.get("args", {}).get("model") or template.model_config.model,
                temperature=template.model_config.temperature
            )

            # Validate response is in choices
            result = response.strip()
            if result not in choices:
                # Try case-insensitive match
                result = self._match_choice(result, choices)

            results.append({"id": item["id"], "result": result})

        return results

    def _find_choices_param(self, template: LLMToolTemplate) -> str:
        """Find the parameter that contains the choices list"""
        # Look for array parameter (categories, tags, options, etc.)
        for param_name, param_def in template.parameters.items():
            if param_def.type == "array" and param_name != "input":
                return param_name
        raise ValueError("No choices parameter found")


# src/tools/operations/multi_label.py
class MultiLabelOperation(OperationStrategy):
    """Handles multi-label operations (tag)"""
    # Similar structure but returns list of labels
    pass


# src/tools/operations/extraction.py
class ExtractionOperation(OperationStrategy):
    """Handles extraction operations"""
    # Handles both simple fields and structured schemas
    pass
```

### 3. **Unified Executor (Zero if-elif)**

```python
# src/tools/llm_tool_executor.py
class LLMToolExecutor:
    """
    Unified executor using strategy pattern.
    No tool-specific code - completely generic.
    """

    # Operation strategy registry
    STRATEGIES = {
        OperationType.SINGLE_CHOICE: SingleChoiceOperation(),
        OperationType.MULTI_LABEL: MultiLabelOperation(),
        OperationType.EXTRACTION: ExtractionOperation(),
    }

    def __init__(self, template: LLMToolTemplate):
        self.template = template
        self.strategy = self.STRATEGIES.get(template.operation_type)
        if not self.strategy:
            raise ValueError(f"Unknown operation type: {template.operation_type}")

    async def execute(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute using appropriate strategy.
        No if-elif needed!
        """
        # Normalize input
        normalized = InputNormalizer.normalize(kwargs.get("input"))

        # Validate parameters
        self.strategy.validate_params(self.template, kwargs)

        # Execute using strategy
        return await self.strategy.execute(
            llm_client=get_llm_client(),
            template=self.template,
            normalized_input=normalized,
            **kwargs
        )
```

### 4. **Template Loader with Pydantic Validation**

```python
# src/tools/template_loader.py
class TemplateLoader:
    """Load and validate tool templates"""

    def _load_all_templates(self):
        """Load JSON files and validate with Pydantic"""
        for json_file in self.templates_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)

            # Pydantic validation - automatic type checking!
            template = LLMToolTemplate.model_validate(data)
            self._templates[template.tool_name] = template
```

### 5. **Updated JSON Config**

```json
{
  "tool_name": "classify_by_llm",
  "operation_type": "single_choice",  // 👈 Strategy selector
  "description": "Classify text into one category",
  "category": "classification",
  "version": "1.0.0",

  "model_config": {
    "provider": "openai",
    "model": "openai/gpt-4o-mini",
    "temperature": 0.0,
    "max_tokens": 100
  },

  "prompt_templates": {
    "system": "You are a classifier. Pick ONE from the list.",
    "user": "Categories: {categories}\nText: {text}\nCategory:"
  },

  "parameters": {
    "input": {
      "type": "array",
      "description": "Items to classify",
      "required": true
    },
    "categories": {  // 👈 Strategy will auto-detect this as choices
      "type": "array",
      "description": "Available categories",
      "required": true
    },
    "prompt": {
      "type": "string",
      "description": "Custom instructions",
      "required": false
    }
  }
}
```

---

## Benefits Over Current System

### ✅ **Scalability**
- **Current:** Need to modify `execute()` for each new tool
- **New:** Just add JSON with `operation_type` - zero code changes

### ✅ **Reusability**
- **Current:** 3 tools = 3 `_execute_*` methods
- **New:** 3 operations = infinite tools

### ✅ **Type Safety**
- **Current:** Plain JSON, no validation
- **New:** Pydantic models with automatic validation

### ✅ **Extensibility**
Add new operation type:
```python
class RankingOperation(OperationStrategy):
    async def execute(self, ...):
        # Ranking logic
        pass

# Register once
LLMToolExecutor.STRATEGIES[OperationType.RANKING] = RankingOperation()
```

Now ANY tool with `"operation_type": "ranking"` works automatically!

### ✅ **Maintainability**
- Single source of truth per operation type
- Test operations, not individual tools
- Clear separation of concerns

---

## Migration Path

1. **Add Pydantic models** (`src/tools/models.py`)
2. **Create operation strategies** (`src/tools/operations/`)
3. **Update LLMToolExecutor** to use strategies
4. **Add `operation_type` to JSON configs**
5. **Update TemplateLoader** to use Pydantic validation
6. **Test each operation type**
7. **Remove old `_execute_*` methods**

---

## Result

### Adding a New Tool
**Before:**
```python
elif tool_name == "my_tool":
    return await self._execute_my_tool(**kwargs)

async def _execute_my_tool(self, ...):
    # 50 lines of code
```

**After:**
```json
{
  "tool_name": "my_tool",
  "operation_type": "single_choice",  // Use existing strategy
  ...
}
```

**That's it!** ✅

### Adding a New Operation Type
Just implement `OperationStrategy` once, register it, and ALL future tools can use it!

---

**Should I implement this improved architecture?** 🚀
