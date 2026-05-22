STYLE_EXTRACTION_PROMPT = """\
You are a code style analyst. Analyze the following Python source file and return a JSON object describing its style. Be precise and concise.

Return ONLY valid JSON with this exact schema:
{{
  "naming": {{
    "functions": "<snake_case|camelCase|PascalCase|other>",
    "classes": "<snake_case|camelCase|PascalCase|other>",
    "variables": "<snake_case|camelCase|PascalCase|other>",
    "constants": "<UPPER_SNAKE_CASE|other>",
    "notes": "<any notable patterns, e.g. verb_noun for functions, single-letter loop vars, etc.>"
  }},
  "structure": {{
    "import_style": "<grouped|flat|alphabetical|none>",
    "class_method_order": "<init_first|alphabetical|public_then_private|none>",
    "preferred_length": "<short|medium|long>",
    "module_layout": "<description of top-level ordering>"
  }},
  "comments": {{
    "docstring_style": "<Google|NumPy|reStructuredText|plain|none>",
    "inline_density": "<sparse|moderate|heavy|none>",
    "docstring_sections": [<list of sections used, e.g. "Args", "Returns", "Raises", "Example">]
  }},
  "representative_snippets": [<1-3 short verbatim code snippets that best show the style>]
}}

Source file ({filename}):
```python
{source}
```
"""

STYLE_SUMMARY_PROMPT = """\
You are a code style analyst. Below are JSON style observations extracted from multiple files in a codebase. Synthesize them into a single authoritative style profile JSON.

Use the same schema. For fields where files disagree, pick the majority or most consistent value. Add a "confidence" field (low/medium/high) per section. Keep representative_snippets to the 3 best examples across all files.

Return ONLY valid JSON.

Observations:
{observations}
"""

CODE_GENERATION_PROMPT = """\
You are an expert Python developer. Write code that matches the style profile below exactly.

Style profile:
{style_profile}

Task:
{task}

Rules:
- Match naming conventions, docstring style, and comment density from the profile exactly.
- Follow the module and class structure patterns.
- Use the representative snippets as a style reference.
- Return ONLY the Python code, no explanation.
"""
