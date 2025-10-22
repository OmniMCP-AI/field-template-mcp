# Field Template Specification

This directory contains field template configurations for the AI Table system. Each template follows a **separated file structure** for better maintainability and performance.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [File Structure](#file-structure)
- [Operation Types](#operation-types)
- [File Specifications](#file-specifications)
- [Schema Design Principles](#schema-design-principles)
- [Examples](#examples)
- [Best Practices](#best-practices)

---

## Architecture Overview

Field templates enable spreadsheet-like "map/lambda function" execution on dataframe rows. Each template consists of three separated files:

```
configs/tools/
├── extract_by_llm/
│   ├── metadata.json      # Marketplace listing (lightweight)
│   ├── tool.json          # Execution spec (MCP/OpenAPI compatible)
│   └── ui.json            # UI configuration (rendering)
├── call_mcp_tool/
│   ├── metadata.json
│   ├── tool.json
│   └── ui.json
└── calculate_formula/
    ├── metadata.json
    ├── tool.json
    └── ui.json
```

### Unified Configuration Pattern

All three operation types follow a **consistent pattern**:

```json
{
  "operation_type": "AItool | mcptool | formula",
  "inputSchema": {/* What user provides */},
  "executor_config": {/* How tool executes */},
  "outputSchema": {/* What tool returns */}
}
```

**Key Principle**: `executor_config` contains **execution-specific configuration**, separate from user inputs:

| Operation Type | `executor_config` Contains |
|----------------|---------------------------|
| **AItool** | `model`, `temperature`, `max_tokens` |
| **mcptool** | `server_url`, `tool_name`, `timeout`, `retry` |
| **formula** | `code`, `engine` (type, version, extensions) |

This separation ensures:
- ✅ `inputSchema` = User inputs (validated by JSON Schema)
- ✅ `executor_config` = System execution settings (engine-specific)
- ✅ Consistent structure across all operation types

**Visual Structure**:

```
┌─────────────────────────────────────────────────────────────┐
│ tool.json                                                   │
├─────────────────────────────────────────────────────────────┤
│ inputSchema          │ What user configures in UI          │
│   ├─ input           │ (Field selections, text inputs)     │
│   ├─ item_to_extract │                                     │
│   └─ args.context    │ Runtime context (baseId, etc.)      │
├──────────────────────┼─────────────────────────────────────┤
│ executor_config      │ How execution happens               │
│  ┌─ AItool ────────┐ │ model, temperature, max_tokens      │
│  ├─ mcptool ────────┤ │ server_url, tool_name, timeout      │
│  └─ formula ────────┘ │ code, engine (type, version)        │
├──────────────────────┼─────────────────────────────────────┤
│ outputSchema         │ What gets written to cell           │
│   ├─ result          │ (Main output value)                 │
│   ├─ code            │ (Status code)                       │
│   └─ message         │ (Status message)                    │
└─────────────────────────────────────────────────────────────┘
```

### Why Separate Files?

1. **Performance**: Marketplace only loads `metadata.json` (fast)
2. **Single Responsibility**: Each file has one clear purpose
3. **Independent Updates**: Change UI without touching execution logic
4. **Lazy Loading**: Load `tool.json` and `ui.json` only when needed
5. **Scalability**: Efficient for large template libraries (100+ templates)

---

## File Structure

### Directory Layout

```
tool_name/
├── metadata.json    # Marketplace display (required)
├── tool.json        # Execution specification (required)
└── ui.json          # User interface configuration (required)
```

### File Loading Strategy

```typescript
// 1. Marketplace loads only metadata
const marketplace = await loadMetadata('**/metadata.json');

// 2. When user selects template, load full config
const template = {
  ...await loadFile('tool_name/metadata.json'),
  tool: await loadFile('tool_name/tool.json'),
  ui: await loadFile('tool_name/ui.json')
};
```

---

## Operation Types

Field templates support three operation types, each with different execution models:

### 1. AItool (LLM-based Processing)

Uses LLM to process text with prompts. You control both `inputSchema` and `formItems`.

**Use cases**: Text extraction, classification, summarization, generation

**Example**: `extract_by_llm`

```json
{
  "operation_type": "AItool",
  "prompt_templates": {
    "system": "You are a data extraction expert...",
    "user": "Extract {item_to_extract} from: {input}"
  }
}
```

### 2. mcptool (External MCP Tool Call)

Calls external MCP server. `inputSchema` is fetched from server, `formItems` provides UI interpretation.

**Use cases**: Integration with external services, API calls, complex processing

**Example**: `call_mcp_tool`

```json
{
  "operation_type": "mcptool",
  "mcp_config": {
    "server_url": "mcp://localhost:3000",
    "tool_name": "extract_data"
  }
}
```

### 3. formula (Spreadsheet Formula)

Executes Nunjucks templates with field references. No `inputSchema` validation, `formItems` defines field selections.

**Use cases**: Calculations, comparisons, string manipulation, date math

**Example**: `calculate_formula`

```json
{
  "operation_type": "formula",
  "formula_template": "IF([{$ field1.name $}]>0, \"Yes\", \"No\")"
}
```

---

## File Specifications

### metadata.json

**Purpose**: Marketplace listing and discovery

**Schema**:
```json
{
  "id": "string (unique identifier)",
  "displayName": {
    "en-US": "English name",
    "zh-CN": "中文名称"
  },
  "description": {
    "en-US": "English description",
    "zh-CN": "中文描述"
  },
  "category": "AI Field | Utility | Efficiency tools | Project Management | ...",
  "icon": "emoji or URL",
  "version": "semver string",
  "provider": "system | user | organization",
  "tags": ["array", "of", "tags"],
  "featured": true | false,
  "_refs": {
    "tool": "./tool.json",
    "ui": "./ui.json"
  }
}
```

**Categories**:
- `AI Field`: LLM-powered processing
- `Utility`: General-purpose tools
- `Efficiency tools`: Productivity helpers
- `Project Management`: Task/project tools
- `Teamwork`: Collaboration features
- `Recruitment`: HR-related tools

---

### tool.json

**Purpose**: Execution specification (MCP/OpenAPI compatible)

**Common Fields**:
```json
{
  "name": "tool_name",
  "operation_type": "AItool | mcptool | formula",
  "description": "Tool description",
  "inputSchema": {
    "type": "object",
    "properties": {
      "...user_inputs...",
      "args": {
        "type": "object",
        "description": "Optional runtime context (provided by system)",
        "properties": {
          "context": {
            "type": "object",
            "properties": {
              "baseId": {"type": "string"},
              "worksheetId": {"type": "string"}
            }
          }
        }
      }
    },
    "required": ["...user_inputs..."]
  },
  "executor_config": {
    /* Operation-specific execution configuration */
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "result": { "type": "string" },
      "code": { "type": "integer" },
      "message": { "type": "string" }
    }
  },
  "examples": [ ... ]
}
```

**Note**: All `inputSchema` must include `args.context` for runtime context (baseId, worksheetId). This is provided by the system at execution time, not configured by users.

#### AItool Specific Fields:
```json
{
  "operation_type": "AItool",
  "prompt_templates": {
    "system": "System prompt template",
    "user": "User prompt template with {variables}"
  },
  "executor_config": {
    "model": {
      "type": "string",
      "enum": ["gpt-4o-mini", "qwen-3.0-plus"],
      "default": "gpt-4o-mini"
    },
    "temperature": {
      "type": "number",
      "default": 0.0
    },
    "max_tokens": {
      "type": "integer",
      "default": 1000
    }
  },
  "inputSchema": {
    "properties": {
      "input": {
        "type": "string",
        "description": "Main input field"
      },
      "args": {
        "type": "object",
        "description": "Optional runtime context",
        "properties": {
          "context": {
            "type": "object",
            "properties": {
              "baseId": {"type": "string"},
              "worksheetId": {"type": "string"}
            }
          }
        }
      }
    },
    "required": ["input"]
  }
}
```

#### mcptool Specific Fields:
```json
{
  "operation_type": "mcptool",
  "executor_config": {
    "server_url": "mcp://host:port",
    "tool_name": "tool_id",
    "timeout": 30000,
    "retry": {
      "enabled": true,
      "max_attempts": 3,
      "backoff": "exponential"
    }
  },
  "inputSchema": {
    "description": "Fetched from MCP server at runtime",
    "_note": "This is placeholder/cached version. Always includes args.context",
    "properties": {
      "...mcp_tool_params...",
      "args": {
        "type": "object",
        "properties": {
          "context": {
            "type": "object",
            "properties": {
              "baseId": {"type": "string"},
              "worksheetId": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

**Note**: `operation_type: "mcptool"` implies execution type is `mcp_call`. No need for separate `execution.type` field.

#### formula Specific Fields:
```json
{
  "operation_type": "formula",
  "executor_config": {
    "code": "IF([{$ field1.name $}]>0, \"Yes\", \"No\")",
    "engine": {
      "type": "nunjucks",
      "version": "3.x",
      "extensions": {
        "field_reference": true,
        "custom_filters": ["round", "abs", "max", "min"]
      }
    }
  },
  "inputSchema": {
    "properties": {
      "args": {
        "type": "object",
        "properties": {
          "context": {
            "type": "object",
            "properties": {
              "baseId": {"type": "string"},
              "worksheetId": {"type": "string"}
            }
          }
        }
      }
    }
  },
  "supported_functions": [
    "IF(condition, true_val, false_val)",
    "IFS(cond1, val1, cond2, val2, ...)",
    "AND(...)", "OR(...)", "NOT(...)",
    "TODAY()", "ROUND(num, decimals)",
    "CONCAT(...)", "EXACT(str1, str2)"
  ]
}
```

**Note**: `operation_type: "formula"` implies execution type is `nunjucks_template`. Runtime context includes current row fields and table info.

---

## Runtime Context & Execution

### Standard `args.context` Structure

All field templates receive runtime context from the system:

```json
{
  "args": {
    "context": {
      "baseId": "table_abc123",      // Current AI table ID
      "worksheetId": "sheet_xyz789"   // Current worksheet/sheet ID
    }
  }
}
```

**Purpose**:
- **Logging & Auditing**: Track which table/sheet triggered execution
- **Multi-tenancy**: Scope data access and permissions by table
- **Rate Limiting**: Apply quotas per-table or per-sheet
- **Error Tracking**: Include context in error reports

**Example Usage in Runtime**:
```typescript
async function executeFieldTemplate(config, formData, runtimeContext) {
  const input = {
    ...formData,
    args: {
      context: {
        baseId: runtimeContext.table.id,
        worksheetId: runtimeContext.sheet.id
      }
    }
  };

  logger.info('Executing template', {
    template: config.name,
    table: input.args.context.baseId,
    sheet: input.args.context.worksheetId
  });

  return await execute(config, input);
}
```

### How Field References Are Resolved

Field templates don't directly access row data in config. The runtime system resolves field references:

```typescript
// 1. User configures in UI
const formData = {
  source_field: "name",  // User selected "name" field
  item_to_extract: "email"
};

// 2. System provides runtime context
const runtimeContext = {
  currentRow: {
    id: "row_123",
    fields: {
      name: "John Doe",
      email: "john@example.com",
      phone: "555-1234"
    }
  },
  table: {id: "table_abc", name: "Users"},
  sheet: {id: "sheet_xyz", name: "Sheet1"}
};

// 3. Runtime executor resolves field values
const resolvedInput = {
  input: runtimeContext.currentRow.fields[formData.source_field],
  // Result: "John Doe"

  item_to_extract: formData.item_to_extract,
  // Result: "email"

  args: {
    context: {
      baseId: runtimeContext.table.id,
      worksheetId: runtimeContext.sheet.id
    }
  }
};

// 4. Execute tool with resolved input
const result = await executeTool(config, resolvedInput);
```

### Execution Type Mapping

`operation_type` determines how the tool executes:

| `operation_type` | Execution Type | Runtime Behavior |
|------------------|----------------|------------------|
| `AItool` | `llm_call` | Renders prompts → calls LLM → returns result |
| `mcptool` | `mcp_call` | Resolves fields → calls MCP server → returns result |
| `formula` | `nunjucks_template` | Renders template with field values → evaluates → returns result |

**No need for separate `execution.type` field** - it's directly inferred from `operation_type`.

---

### ui.json

**Purpose**: User interface configuration (completely separate from tool.json)

**Schema**:
```json
{
  "fieldType": "text | number | singleSelect | multiSelect | ...",
  "fieldConfig": {
    "type": "text",
    "autoUpdate": true,
    "resultPath": "result",
    "recalculate_on": ["field_change", "row_add"]
  },
  "uiSchema": {
    "fieldMetaEditor": {
      "component": "FieldMetaEditor",
      "props": {
        "schema": {
          "items": [
            {
              "key": "field_name",
              "label": {
                "en-US": "Label",
                "zh-CN": "标签"
              },
              "component": "FieldSelect | Textarea | SingleSelect | NumberInput | Checkbox | ...",
              "props": {
                "mode": "single | multiple",
                "supportTypes": ["text", "number", ...],
                "options": [...],
                "placeholder": "...",
                "defaultValue": "...",
                "rows": 3,
                "enableFieldReference": true
              },
              "validator": {
                "required": true | false,
                "pattern": "regex"
              },
              "tooltips": {
                "title": {
                  "en-US": "Help text",
                  "zh-CN": "帮助文本"
                }
              },
              "_schemaRef": "inputSchema.properties.field_name"
            }
          ]
        }
      }
    }
  }
}
```

**Note**: The `uiSchema.fieldMetaEditor` wrapper follows the DingTalk reference spec. The `items` array contains the actual form fields configuration.

#### UI Components

| Component | Purpose | Props |
|-----------|---------|-------|
| `FieldSelect` | Select table fields | `mode`, `supportTypes` |
| `Textarea` | Multi-line text input | `placeholder`, `rows`, `enableFieldReference` |
| `SingleSelect` | Dropdown single selection | `options`, `defaultValue` |
| `MultiSelect` | Dropdown multi selection | `options`, `defaultValue` |
| `Radio` | Radio button group | `options`, `defaultValue` |
| `Checkbox` | Boolean checkbox | `defaultValue` |
| `NumberInput` | Number input | `min`, `max`, `step`, `defaultValue` |
| `ReadonlyText` | Display-only text | `placeholder` |

#### Field Type Mapping

Maps `outputSchema` to spreadsheet field types:

| outputSchema.result.type | fieldType |
|-------------------------|-----------|
| `string` | `text` |
| `number`, `integer` | `number` |
| `boolean` | `checkbox` |
| `array` (with string items) | `multiSelect` |
| `object` | `object` |
| `string` with `enum` | `singleSelect` |

---

## Schema Design Principles

### 1. Complete Separation (Option 3)

**inputSchema** and **uiSchema** serve different purposes:

| Concern | inputSchema (tool.json) | uiSchema (ui.json) |
|---------|------------------------|---------------------|
| Purpose | Validation & execution | UI rendering |
| Format | OpenAPI/JSON Schema | DingTalk UI schema format |
| Audience | Runtime engine | UI renderer |
| Updates | Changes affect logic | Changes affect UX only |

### 2. Linking with `_schemaRef`

UI items reference schema properties for validation:

```json
{
  "uiSchema": {
    "fieldMetaEditor": {
      "component": "FieldMetaEditor",
      "props": {
        "schema": {
          "items": [
            {
              "key": "text",
              "component": "FieldSelect",
              "_schemaRef": "inputSchema.properties.text"
            }
          ]
        }
      }
    }
  }
}
```

**Note**: The `items` array inside `uiSchema.fieldMetaEditor.props.schema` is what we refer to as "formItems" - it's the actual form field definitions.

### 3. For mcptool: External Schema + Custom UI

```
┌────────────────────────┐
│ MCP Server             │
│ (tools/list)           │
└───────┬────────────────┘
        │ Fetches inputSchema
        ↓
┌────────────────────────┐
│ tool.json              │
│ - inputSchema (cached) │
│ - executor_config      │
└────────────────────────┘
        +
┌────────────────────────┐
│ ui.json                │
│ - uiSchema             │  ← Your UI interpretation
│   - items[]            │  ← Form field definitions
│   - _schemaRef links   │
└────────────────────────┘
```

### 4. For AItool/formula: UI Generated from Schema

```
┌────────────────────────┐
│ tool.json              │
│ - inputSchema          │  ← Source of truth
└───────┬────────────────┘
        │ Can auto-generate
        ↓
┌────────────────────────┐
│ ui.json                │
│ - uiSchema.items[]     │  ← Can be generated or explicit
└────────────────────────┘
```

---

## Examples

### Example 1: AItool (extract_by_llm)

**metadata.json**:
```json
{
  "id": "extract_by_llm",
  "displayName": {"en-US": "Information Extraction"},
  "category": "AI Field",
  "icon": "🔍"
}
```

**tool.json**:
```json
{
  "operation_type": "AItool",
  "executor_config": {
    "model": {
      "type": "string",
      "enum": ["gpt-4o-mini", "qwen-3.0-plus"],
      "default": "gpt-4o-mini"
    },
    "temperature": {"type": "number", "default": 0.0},
    "max_tokens": {"type": "integer", "default": 1000}
  },
  "inputSchema": {
    "properties": {
      "input": {"type": "string"},
      "item_to_extract": {"type": "string"},
      "args": {
        "type": "object",
        "properties": {
          "context": {
            "type": "object",
            "properties": {
              "baseId": {"type": "string"},
              "worksheetId": {"type": "string"}
            }
          }
        }
      }
    },
    "required": ["input", "item_to_extract"]
  },
  "prompt_templates": {
    "system": "Extract {item_to_extract} from the text",
    "user": "{input}"
  }
}
```

**ui.json**:
```json
{
  "fieldType": "text",
  "uiSchema": {
    "fieldMetaEditor": {
      "component": "FieldMetaEditor",
      "props": {
        "schema": {
          "items": [
            {
              "key": "input",
              "component": "FieldSelect",
              "props": {"supportTypes": ["text"]},
              "_schemaRef": "inputSchema.properties.input"
            },
            {
              "key": "item_to_extract",
              "component": "Textarea",
              "_schemaRef": "inputSchema.properties.item_to_extract"
            }
          ]
        }
      }
    }
  }
}
```

### Example 2: mcptool (call_mcp_tool)

**tool.json**:
```json
{
  "operation_type": "mcptool",
  "executor_config": {
    "server_url": "mcp://localhost:3000",
    "tool_name": "extract_data"
  },
  "inputSchema": {
    "_note": "Fetched from MCP server"
  }
}
```

**ui.json**:
```json
{
  "uiSchema": {
    "fieldMetaEditor": {
      "component": "FieldMetaEditor",
      "props": {
        "schema": {
          "items": [
            {
              "key": "source_field",
              "component": "FieldSelect",
              "_schemaRef": "inputSchema.properties.text",
              "_note": "Maps to external MCP tool parameter"
            }
          ]
        }
      }
    }
  }
}
```

### Example 3: formula (calculate_formula)

**tool.json**:
```json
{
  "operation_type": "formula",
  "executor_config": {
    "code": "IF([{$ field1.name $}]>0, \"Yes\", \"No\")",
    "engine": {
      "type": "nunjucks",
      "version": "3.x",
      "extensions": {
        "field_reference": true,
        "custom_filters": ["round", "abs", "max", "min"]
      }
    }
  },
  "supported_functions": ["IF", "AND", "OR", "TODAY", "ROUND"]
}
```

**ui.json**:
```json
{
  "fieldType": "formula",
  "uiSchema": {
    "fieldMetaEditor": {
      "component": "FieldMetaEditor",
      "props": {
        "schema": {
          "items": [
            {
              "key": "field1",
              "component": "FieldSelect",
              "props": {"supportTypes": ["number"]}
            },
            {
              "key": "formula_template",
              "component": "Textarea",
              "props": {
                "enableSyntaxHighlight": true,
                "syntaxType": "nunjucks"
              }
            }
          ]
        }
      }
    }
  }
}
```

---

## Best Practices

### 1. File Organization

✅ **DO**: Use separate files for templates with complex UI
✅ **DO**: Keep metadata.json lightweight (< 1KB)
✅ **DO**: Cache tool.json for mcptool (avoid repeated fetches)

❌ **DON'T**: Duplicate information across files
❌ **DON'T**: Include large data in metadata.json

### 2. Schema Design

✅ **DO**: Follow OpenAPI/JSON Schema standards in tool.json
✅ **DO**: Use `_schemaRef` to link formItems to inputSchema
✅ **DO**: Provide comprehensive `examples` in tool.json

❌ **DON'T**: Mix UI concerns into inputSchema
❌ **DON'T**: Duplicate validation rules

### 3. UI Configuration

✅ **DO**: Use i18n for all user-facing text
✅ **DO**: Provide helpful tooltips and placeholders
✅ **DO**: Set sensible defaults in props.defaultValue

❌ **DON'T**: Hardcode language-specific strings
❌ **DON'T**: Create confusing field names

### 4. Internationalization

```json
{
  "label": {
    "en-US": "Source field",
    "zh-CN": "源字段",
    "ja-JP": "ソースフィールド"
  }
}
```

Supported languages: `en-US`, `zh-CN`, `ja-JP`

### 5. Validation

```json
{
  "validator": {
    "required": true,
    "pattern": "^[a-zA-Z0-9_]+$",
    "custom": "validateFieldName"
  }
}
```

### 6. Error Handling

**tool.json** should define error codes:
```json
{
  "outputSchema": {
    "properties": {
      "code": {
        "type": "integer",
        "enum": [0, 1, 2, 3],
        "description": "0=success, 1=validation_error, 2=execution_error, 3=timeout"
      }
    }
  }
}
```

---

## Migration Guide

### From Single File to Separated Files

**Before** (single file):
```json
{
  "tool_name": "extract",
  "description": "...",
  "category": "extraction",
  "inputSchema": {...},
  "outputSchema": {...},
  "formItems": [...]
}
```

**After** (separated):

**metadata.json**:
```json
{
  "id": "extract",
  "displayName": {"en-US": "Extract"},
  "category": "AI Field"
}
```

**tool.json**:
```json
{
  "name": "extract",
  "inputSchema": {...},
  "outputSchema": {...}
}
```

**ui.json**:
```json
{
  "formItems": [...]
}
```

---

## Runtime Loading

```typescript
// Loader implementation
async function loadTemplate(templateId: string) {
  const basePath = `configs/tools/${templateId}`;

  // 1. Load metadata (required)
  const metadata = await loadJSON(`${basePath}/metadata.json`);

  // 2. Load tool spec (required)
  const tool = await loadJSON(`${basePath}/tool.json`);

  // 3. Load UI config (required)
  const ui = await loadJSON(`${basePath}/ui.json`);

  // 4. For mcptool: Fetch live schema
  if (tool.operation_type === 'mcptool') {
    const liveSchema = await fetchMCPToolSchema(
      tool.executor_config.server_url,
      tool.executor_config.tool_name
    );
    tool.inputSchema = liveSchema;
  }

  // 5. Validate consistency
  validateFormItemsAgainstSchema(ui.uiSchema.fieldMetaEditor.props.schema.items, tool.inputSchema);

  return { metadata, tool, ui };
}
```

---

## Contributing

When creating new field templates:

1. Create directory: `configs/tools/your_tool_name/`
2. Add three required files: `metadata.json`, `tool.json`, `ui.json`
3. Follow the schemas documented above
4. Test with all operation types if applicable
5. Provide comprehensive examples
6. Add i18n for all user-facing text

---

## Version History

- **v1.0.0** (2025-01-22): Initial separated file structure
  - Separated metadata, tool, and UI configurations
  - Support for AItool, mcptool, and formula operation types
  - Complete separation of concerns (Option 3)
  - OpenAPI/MCP compatible schemas

---

## See Also

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [JSON Schema](https://json-schema.org/)
- [Nunjucks Template Engine](https://mozilla.github.io/nunjucks/)
