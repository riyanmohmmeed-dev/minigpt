# Seed problems

Each file is a JSON array of seed items. One item:

```json
{
  "id": "unique-id",
  "instruction": "User-facing prompt, e.g. Write a Python function to ...",
  "language": "python",
  "topic": "strings",
  "hint": "Optional hint for the teacher to vary the problem"
}
```

- **instruction**: The task we want the model to learn (will be expanded/varied by teacher).
- **language**: Target language (python, javascript, etc.).
- **topic**: Rough category for filtering (strings, algorithms, api, etc.).
- **hint**: Optional; used by the expansion script to ask the teacher for variations.

Files: `seeds_*.json`. Example: `seeds_python_basics.json`.
