---
description: Analyze a codebase's coding style and generate a style_profile.json
argument-hint: [path]
---

# analyze

Analyze the target directory's codebase to extract coding style conventions and generate a `style_profile.json` at the repository root.

## Instructions

The directory to analyze is `$ARGUMENTS`. If that is empty, analyze the current project root.

1. **Glob the target directory** for source files. Skip any path containing:
   - `__pycache__`
   - `.git`
   - `node_modules`
   - `dist`
   - `build`
   - `venv`

2. **Identify the dominant source language(s)** by examining file extensions and structure.

3. **Read a representative SAMPLE ONLY** — do NOT read every file in the repository. A representative sample consists of:
   - Entry points (main files, `__init__.py`, `index.ts`, etc.)
   - The largest/most complex modules
   - A few leaf files (utilities, helpers, simple implementations)
   
   Reading every file is unnecessary and wasteful. Focus on getting representative patterns.

4. **Write `style_profile.json` to the current project root** — always that root, even when a different
   directory was analyzed. That is the only place the `mycode-style` skill reads it from. Use the schema
   described below, omitting any section that does not apply to the detected language(s).

5. **For multi-language repositories**, key the top level by language: `{"python": {...}, "typescript": {...}}`. For single-language repositories, put the schema sections directly at the top level with no language wrapper.

## Schema

The following schema defines the structure of `style_profile.json`. Each section contains key-value pairs with short descriptive strings as values, EXCEPT where noted:

### naming
- `functions`: Pattern for function naming (e.g., "snake_case")
- `classes`: Pattern for class naming (e.g., "PascalCase")
- `variables`: Pattern for variable naming (e.g., "snake_case")
- `constants`: Pattern for constant naming (e.g., "UPPER_SNAKE_CASE")
- `private_prefix`: Convention for private members (e.g., "_prefix" or "private_" keyword)
- `notes`: Any additional naming conventions

### type_annotations (omit entirely if language is untyped)
- `usage`: How frequently types are used (e.g., "full", "partial", "sparse")
- `union_syntax`: Union type syntax (e.g., "Type | None" or "Optional[Type]")
- `return_annotations`: Whether return types are annotated (e.g., "always", "for_public_only")
- `builtin_generics`: How built-in generic types are used (e.g., "list[T]" or "List[T]")

### structure
- `import_grouping`: How imports are organized (e.g., "stdlib, third-party, local")
- `constants_placement`: Where constants are defined (e.g., "module level")
- `class_method_order`: Order of methods in classes (e.g., "__init__, public, private")
- `main_guard`: Whether `if __name__ == "__main__":` pattern is used
- `preferred_length`: Preferred line/file length guidelines (e.g., "80-char lines, <500 line files")

### error_handling
- `exit_style`: How programs exit (e.g., "sys.exit()", "raise SystemExit()")
- `exception_types`: **Array of strings** listing commonly used exception types (e.g., `["ValueError", "RuntimeError", "KeyError"]`)
- `guard_style`: Error prevention pattern (e.g., "raise early", "LBYL", "EAFP")
- `error_messages`: Format of error messages (e.g., "descriptive with context")

### strings_and_flow
- `string_formatting`: Preferred string formatting (e.g., "f-strings", ".format()", "%")
- `comprehensions`: Use of comprehensions (e.g., "preferred for all iterables")
- `method_chaining`: Whether methods chain (e.g., "avoided", "common")
- `ternary`: Whether ternary expressions are used (e.g., "rarely", "common")

### comments
- `docstring_style`: Docstring format (e.g., "Google style", "NumPy style", "PEP 257")
- `docstring_coverage`: Scope of docstring usage (e.g., "all functions and classes", "public only")
- `inline_density`: How frequently inline comments appear (e.g., "sparse", "moderate", "dense")
- `inline_style`: Inline comment style (e.g., "explain why, not what")

### representative_snippets
- **Array of 1-3 strings**: VERBATIM code snippets copied directly from the analyzed codebase that exemplify the identified style patterns.

## Example

A single-language Python repository. For a multi-language repository, wrap one of these objects
per language under a language key — `{"python": { ...as below... }, "typescript": { ... }}` — and
drop or adapt the sections that do not apply to each language.

```json
{
  "naming": {
    "functions": "snake_case",
    "classes": "PascalCase",
    "variables": "snake_case",
    "constants": "UPPER_SNAKE_CASE",
    "private_prefix": "_prefix",
    "notes": "Private methods prefixed with single underscore; internal use only"
  },
  "type_annotations": {
    "usage": "full",
    "union_syntax": "Type | None",
    "return_annotations": "always",
    "builtin_generics": "list[T]"
  },
  "structure": {
    "import_grouping": "stdlib, third-party, local with blank lines between",
    "constants_placement": "module level at top after imports",
    "class_method_order": "__init__, public methods, private methods, dunder methods",
    "main_guard": "if __name__ == '__main__': pattern used",
    "preferred_length": "88-char lines (Black default), files typically under 300 lines"
  },
  "error_handling": {
    "exit_style": "sys.exit(code) for scripts, raise Exception for libraries",
    "exception_types": ["ValueError", "RuntimeError", "FileNotFoundError", "KeyError"],
    "guard_style": "EAFP (Easier to Ask for Forgiveness than Permission)",
    "error_messages": "Descriptive with context about what went wrong"
  },
  "strings_and_flow": {
    "string_formatting": "f-strings exclusively",
    "comprehensions": "preferred for readable transformations",
    "method_chaining": "avoided; prefer explicit intermediate variables",
    "ternary": "rarely used; prefer full if/else for clarity"
  },
  "comments": {
    "docstring_style": "Google style",
    "docstring_coverage": "all public functions and classes",
    "inline_density": "sparse; only for non-obvious logic",
    "inline_style": "explain why, not what; code should be self-documenting"
  },
  "representative_snippets": [
    "def calculate_total(items: list[float]) -> float:\n    \"\"\"Sum all items with type safety.\"\"\"\n    return sum(items)",
    "class DataProcessor:\n    def __init__(self, data: list[dict]):\n        self._data = data\n    \n    def process(self) -> list[str]:\n        return [item['name'] for item in self._data if item.get('active')]",
    "if __name__ == '__main__':\n    sys.exit(main())"
  ]
}
```

---

Sample widely enough that the profile is representative, then stop reading and write the file.
