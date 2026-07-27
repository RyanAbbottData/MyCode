STYLE_EXTRACTION_PROMPT = """\
You are a code style analyst. Your entire response must be a single valid JSON object.
Do not include any text, greeting, explanation, or markdown before or after the JSON.
Do not use code fences. Start your response with {{ and end it with }}.

Analyze the following Python source file and return a JSON object describing its style using this exact schema:
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

STYLE_MERGE_PROMPT = """\
You are a code style analyst. Your entire response must be a single valid JSON object.
Do not include any text, greeting, explanation, or markdown before or after the JSON.
Do not use code fences. Start your response with {{ and end it with }}.

Update the current style profile by merging in a new file observation.

Rules:
- Where they agree, keep the value.
- Where they disagree, pick the more consistent value.
- Keep representative_snippets to the 3 best examples total.
- Return ONLY valid JSON using the same schema.

Current profile:
{profile}

New observation ({filename}):
{observation}
"""

LOCAL_STYLE_EXTRACTION_PROMPT = """\
Return ONLY a JSON object, nothing else. No explanation, no markdown.

Example of the exact output format:
{{"naming": "snake_case", "docstrings": "Google", "imports": "grouped", "comments": "sparse", "snippet": "def load_data(path):\\n    return pd.read_csv(path)"}}

Analyze the Python file below. Return a single JSON object with these 5 keys:
- naming: snake_case | camelCase | PascalCase | mixed
- docstrings: Google | NumPy | plain | none
- imports: grouped | flat | alphabetical | none
- comments: sparse | moderate | heavy | none
- snippet: one short code snippet showing the style

File: {filename}
```python
{source}
```
"""

LOCAL_STYLE_MERGE_PROMPT = """\
Return ONLY a JSON object, nothing else. No explanation, no markdown.

Example of the exact output format:
{{"naming": "snake_case", "docstrings": "Google", "imports": "grouped", "comments": "sparse", "snippet": "def load_data(path):\\n    return pd.read_csv(path)"}}

Merge these two style observations. Return a single JSON object with these 5 keys: naming, docstrings, imports, comments, snippet.
Where values agree, keep them. Where they differ, pick the more common value.

Profile A: {profile}

Profile B (from {filename}): {observation}
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
