## Skill: Universal Project Exploration

### Objective
Enable the model to systematically explore any coding project to understand its structure, key files, and purpose.

### Steps

1. **Reveal Project Structure**
   - Use `run_bash` to list directories and files at the root and subdirectories.
   - Commands: `ls`, `tree` (with depth limits to avoid overload).

2. **Identify Critical Files**
   - Look for common project overview and configuration files such as `README`, `LICENSE`, `CHANGELOG`, environment files (`.env`), dependency manifests (`requirements.txt`, `package.json`, `Gemfile`, `pom.xml`, etc.), and main application entry points (e.g., `main.*`, `index.*`).
   - Use `read_file` to inspect these files.

3. **Explore Core Directories**
   - Focus on directories likely containing source code or core logic (e.g., `src`, `lib`, `app`, `services`, `packages`).
   - Read files that define key workflows, classes, functions, or modules.

4. **Trace Dependencies and Configurations**
   - Read project dependency files to understand libraries or frameworks in use.
   - Examine environment or configuration files for keys, endpoints, or parameters that affect project behavior.

5. **Iterative Exploration**
   - Follow references in files to discover other critical files or modules.
   - Prioritize files essential for understanding project functionality and data flow.

### Tools to Use

- **run_bash**: Explore directories and inspect file contents (`ls`, `tree`, `pwd`, `find`).
- **read_file**: Read content of specific files.
- **write_file / edit_file**: Only if you need to modify or create helper files for analysis.

### Guidelines

- Prefer multiple small tool calls over assumptions.
- Focus on files that provide insight into project logic and structure.
- Avoid reading large non-critical files unless referenced by key scripts.
- Maintain a systematic exploration path: root → main directories → key scripts → supporting modules.

### Example Exploration Sequence

1. `run_bash` → `ls -la` at root to reveal top-level directories.
2. `read_file` → project overview files (`README`, `CHANGELOG`).
3. `read_file` → dependency manifests (`requirements.txt`, `package.json`, `Gemfile`, etc.).
4. `run_bash` → explore core directories (`src`, `lib`, `app`, etc.).
5. `read_file` → files defining key logic or workflows.
6. Iterate through referenced modules and files until the project is understood.

This skill allows the model to explore projects of any language or framework, systematically gathering information and understanding the project structure and key functionality using the allowed tools.
