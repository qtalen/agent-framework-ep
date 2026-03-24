# skills_provider Module

## Overview

Provides a skills provider that supports dynamic async updates before each Agent run. Solves the need to load skills from external sources (API, database) at runtime.

## File Structure

```
skills_provider/
├── updatable_skills_provider.py  # Core implementation
└── __init__.py                   # Public API export
```

## Files

### updatable_skills_provider.py

**Classes:**

- `UpdatableSkillsProvider` - Skills provider with async update support
  - Inherits: `SkillsProvider` (from agent_framework)
  
  **Constructor Parameters:**
  - `skill_paths` - Path(s) to skill files
  - `skills` - Initial skills list
  - `script_runner` - Script execution handler
  - `instruction_template` - Template for skill instructions
  - `require_script_approval` - Whether scripts need approval
  - `skills_updater` - **Key parameter**: Async callable `() -> Awaitable[Sequence[Skill]]`
  
  **Key Concept: skills_updater**
  
  Optional async function called before each Agent run to fetch/refresh skills. Enables:
  - Fetching skills from remote APIs
  - Querying databases for dynamic skills
  - Filtering skills based on context/user
  - Lazy loading of skills
  
  **Methods:**
  - `_update()` - Internal: calls `skills_updater()`, merges skills, rebuilds instructions/tools
  - `before_run()` - Hook: calls `_update()` then parent initialization
  
  **Error Handling:** If `skills_updater` fails, logs error but continues (non-blocking)

### __init__.py

**Exports:** `UpdatableSkillsProvider`

## Usage Pattern

```python
async def fetch_skills():
    # Async operation: API call, DB query, etc.
    return [Skill(name="...", description="...", content="...")]

provider = UpdatableSkillsProvider(
    skill_paths="./skills",
    skills_updater=fetch_skills,
)
```

## Notes

- `skills_updater` must be async
- New skills overwrite existing ones by name
- Instructions and tools are rebuilt after each update
- Update failures are logged but don't block execution
