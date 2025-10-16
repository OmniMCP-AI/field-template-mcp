# Tool Configurations

This directory contains JSON configuration files for each MCP tool.

## Structure

Each tool config file includes:

- `tool_name`: Unique identifier for the tool
- `description`: What the tool does
- `category`: Tool category (classification, tagging, extraction, etc.)
- `version`: Tool version
- `model_config`: Default LLM model settings
- `prompt_templates`: System and user prompt templates
- `parameters`: Input parameter definitions
- `output_format`: Expected output structure
- `examples`: Usage examples

## Files

- `classify_by_llm.json` - Classification tool configuration
- `tag_by_llm.json` - Tagging tool configuration
- `extract_by_llm.json` - Extraction tool configuration

## Usage

These configs are loaded by the tool implementations to:
1. Define default behavior
2. Construct prompts
3. Validate inputs/outputs
4. Provide documentation

## Customization

You can modify these configs to:
- Change default models or temperature
- Adjust prompt templates
- Add new parameters
- Update examples
