# Design Notes & Clarifications

## Standard Structure

All field templates follow this consistent structure:

```json
{
  "name": "tool_name",
  "operation_type": "AItool | mcptool | formula",
  "inputSchema": {
    "properties": {
      "...user inputs...",
      "args": {
        "type": "object",
        "properties": {
          "context": {
            "type": "object",
            "properties": {
              "baseId": "string",
              "worksheetId": "string"
            }
          }
        }
      }
    }
  },
  "executor_config": {
    "...operation-specific execution settings..."
  },
  "outputSchema": {
    "properties": {
      "result": "...",
      "code": "integer",
      "message": "string"
    }
  }
}
```

---

## Design Decisions

### 1. `operation_type` vs Removed `execution.type`

**Before** (redundant):
```json
{
  "operation_type": "mcptool",
  "execution": {
    "type": "mcp_call"  // ❌ Duplicates operation_type
  }
}
```

**After** (clean):
```json
{
  "operation_type": "mcptool"
  // execution.type removed - inferred from operation_type
}
```

**Mapping**:
- `operation_type: "AItool"` → execution type is `llm_call`
- `operation_type: "mcptool"` → execution type is `mcp_call`
- `operation_type: "formula"` → execution type is `nunjucks_template`

**Reason**: `execution.type` is always directly derivable from `operation_type`, so it's redundant.

---

### 2. Standard `args.context` in All InputSchemas

**Purpose**: Runtime context provided by the system, not user input.

```json
{
  "args": {
    "type": "object",
    "description": "Optional runtime context",
    "properties": {
      "context": {
        "baseId": "table_123",      // Current AI table ID
        "worksheetId": "sheet_456"   // Current worksheet ID
      }
    }
  }
}
```

**Usage**:
- **Logging**: Track which table/sheet triggered execution
- **Multi-tenancy**: Scope data access by table
- **Audit trails**: Record execution context
- **Rate limiting**: Per-table quotas

**Example**:
```typescript
async function executeField(templateConfig, userInput, context) {
  const executionArgs = {
    ...userInput,
    args: {
      context: {
        baseId: context.currentTable.id,
        worksheetId: context.currentSheet.id
      }
    }
  };

  // Log execution
  logger.info('Executing field template', {
    template: templateConfig.name,
    table: executionArgs.args.context.baseId,
    sheet: executionArgs.args.context.worksheetId
  });

  return await execute(templateConfig, executionArgs);
}
```

---

### 3. Removed `execution` Section

**Before**:
```json
{
  "operation_type": "mcptool",
  "execution": {
    "type": "mcp_call",
    "args_mapping": {
      "text": "{$ context.currentRow.fields[formData.source_field] $}",
      "options": "{$ formData.options $}"
    },
    "context": {
      "fields": "All selected fields with their current row values",
      "table": {"name": "Current table name"}
    }
  }
}
```

**After**: Removed entirely

**Why removed?**

1. **`execution.type`**: Redundant with `operation_type` (see #1)

2. **`execution.args_mapping`**: Not needed in config - this is **runtime logic**, not configuration:
   ```typescript
   // This is runtime code, not config:
   function mapFormDataToToolArgs(formData, context) {
     return {
       text: context.currentRow.fields[formData.source_field],
       options: formData.options
     };
   }
   ```

3. **`execution.context`**: Documentation only - actual runtime context is provided by the system:
   ```typescript
   // Runtime context (provided by system):
   const runtimeContext = {
     currentRow: {
       id: "row_123",
       fields: {
         name: "John Doe",
         email: "john@example.com"
       }
     },
     table: {
       id: "table_123",
       name: "Users"
     },
     sheet: {
       id: "sheet_456",
       name: "Sheet1"
     }
   };
   ```

**Where this logic belongs**:

| Concern | Belongs In |
|---------|-----------|
| Config structure | `tool.json` |
| Runtime context | System provides at execution time |
| Args mapping | Runtime executor code |
| Field resolution | Runtime template engine |

---

## Runtime Execution Flow

### How Context is Used

```typescript
// 1. User configures field template
const formData = {
  source_field: "name",  // User selected "name" field
  item_to_extract: "first_name"
};

// 2. System provides runtime context
const runtimeContext = {
  currentRow: {
    fields: {
      name: "John Doe",
      email: "john@example.com"
    }
  },
  table: {
    id: "table_123",
    name: "Users"
  }
};

// 3. Executor resolves field references
const resolvedInput = {
  input: runtimeContext.currentRow.fields[formData.source_field],  // "John Doe"
  item_to_extract: formData.item_to_extract,  // "first_name"
  args: {
    context: {
      baseId: runtimeContext.table.id,
      worksheetId: runtimeContext.sheet.id
    }
  }
};

// 4. Execute tool
const result = await executeTool(toolConfig, resolvedInput);
```

### For Formula Type

```typescript
// Formula: IF([{$ field1.name $}]>0, "Yes", "No")
const formData = {
  field1: "price"  // User selected "price" field
};

const runtimeContext = {
  currentRow: {
    fields: {
      price: 100,
      cost: 80
    }
  },
  table: {
    name: "Products"
  }
};

// Nunjucks renders template with context:
const templateContext = {
  field1: {
    name: "price",
    value: runtimeContext.currentRow.fields["price"]  // 100
  },
  __context__: {
    table: runtimeContext.table
  }
};

const rendered = nunjucks.renderString(
  toolConfig.executor_config.code,
  templateContext
);
// Result: "IF([price]>0, "Yes", "No")" → "Yes"
```

---

## FAQ

### Q: Why is `args.context` optional?

A: It's provided by the system at runtime. Users don't configure it in the UI. The `args` object is marked as not required in `inputSchema.required`, but the system always includes it.

### Q: What if I need more context information?

A: Extend `args.context` in your implementation:

```json
{
  "args": {
    "context": {
      "baseId": "string",
      "worksheetId": "string",
      "recordId": "string",        // Add if needed
      "userId": "string",          // Add if needed
      "executionId": "string"      // Add if needed
    }
  }
}
```

### Q: Can I use context in formulas?

A: Yes! Context is available in template rendering:

```javascript
// Template can reference context
"Generated for table: {$ __context__.table.name $}"
```

### Q: How do I access field values in mcptool?

A: The runtime executor resolves field references before calling MCP tool:

```typescript
// User configures: source_field = "description"
// System resolves: text = currentRow.fields["description"]
await callMCPTool({
  toolName: "extract_data",
  args: {
    text: "Actual field value from current row",
    options: {...}
  }
});
```

---

## Summary

### Standard Pattern

```
┌──────────────────────────────────────────────────────────┐
│ tool.json                                                │
├──────────────────────────────────────────────────────────┤
│ operation_type    → Determines execution type            │
│                     (AItool→llm_call, mcptool→mcp_call)  │
├──────────────────────────────────────────────────────────┤
│ inputSchema                                              │
│   └─ args.context → Runtime context (always included)    │
├──────────────────────────────────────────────────────────┤
│ executor_config   → Execution settings                   │
│   ├─ AItool: model, temperature, max_tokens             │
│   ├─ mcptool: server_url, tool_name, timeout            │
│   └─ formula: code, engine                              │
├──────────────────────────────────────────────────────────┤
│ outputSchema      → Result structure                     │
│   └─ result, code, message                              │
└──────────────────────────────────────────────────────────┘
```

### What's Removed

- ❌ `execution.type` - Redundant with `operation_type`
- ❌ `execution.args_mapping` - Runtime logic, not config
- ❌ `execution.context` - Provided by system at runtime

### What's Standardized

- ✅ All `inputSchema` have `args.context`
- ✅ `operation_type` is single source of truth
- ✅ `executor_config` contains execution settings
- ✅ Runtime context provided by system, not in config
