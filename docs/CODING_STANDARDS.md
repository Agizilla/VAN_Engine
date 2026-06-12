# Coding Standards

## 10. Language-Specific Guidelines

### Python
- Use type hints for all function signatures (PEP 484).
- Prefer dataclasses over plain dicts for structured data.
- Use `with` for resource management (files, locks, database connections).
- Follow PEP 8 naming: snake_case for variables/functions, PascalCase for classes.
- Use `logging.getLogger(__name__)` — never `print()`.
- For asynchronous I/O, prefer `asyncio` with `async/await` (avoid legacy callback-based libraries).

### C#
- Follow .NET naming conventions: PascalCase for public members, camelCase for parameters and local vars.
- Use `async/await` for I/O operations — never `.Result` or `.Wait()` in production code.
- Prefer dependency injection over static singletons (register services in `IServiceCollection`).
- Use `record` types for immutable DTOs.
- Use `using` declarations or `await using` for disposables.
- Log with `ILogger<T>` — never `Console.WriteLine`.

### JavaScript / jQuery (legacy) & Modern JS
- Avoid jQuery for new features — use native DOM APIs (`querySelector`, `fetch`, `addEventListener`).
- If jQuery must be kept, isolate it in dedicated modules; do not mix with modern framework code.
- Use ES6+ syntax: `const`/`let`, arrow functions, template literals, destructuring.
- Prefer TypeScript over plain JavaScript for any non-trivial frontend.
- For HTTP requests, use `fetch` with proper error handling (check `response.ok`).
- Never inline event handlers in HTML (`onclick="..."`) — use `addEventListener` in script.

## 11. Security Rules (Cross-Language)
- Never log secrets (passwords, API keys, tokens, PII). Sanitize before logging.
- Validate all external input (query strings, JSON body, headers, environment variables) using a schema validator (pydantic/zod/System.Text.Json).
- Use parameterised queries or an ORM — never concatenate user input into SQL.
- Store secrets in environment variables or a secrets manager (never in source control).
- Implement rate limiting on public endpoints to mitigate brute force / DoS.

## 12. Performance & Reliability Guidelines
- Avoid synchronous blocking calls in async contexts (e.g., `Task.Run` in ASP.NET request pipeline).
- Use connection pooling for databases and HTTP clients.
- Implement retries with exponential backoff for transient failures (network, database).
- Use caching (memory, Redis) for expensive reads that tolerate staleness.
- For Python, prefer `asyncio.gather` over sequential `await`s when I/O operations are independent.

## 13. Project Structure & Dependency Management
- Separate concerns: keep UI, business logic, data access, and configuration in distinct modules/layers.
- Use dependency inversion (program to interfaces, not concrete implementations).
- Keep configuration out of code — use environment variables, config files, or a configuration service.
- Pin dependencies to exact versions (commit lock files: `requirements.txt` + `pyproject.toml` for Python; `packages.lock.json` or `*.csproj` with `<PackageReference Version="...">` for C#).

## 14. Git & Commit Conventions
- Use Conventional Commits format: `type(scope): subject`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
- Keep commits atomic (one logical change per commit).
- Write commit messages in imperative present tense ("Add validation", not "Added validation").
- Reference issue/ticket numbers in the commit body when applicable.

## 15. Documentation Standards
- Every public API (function, class, endpoint) must have a docstring/comment describing:
  - Purpose
  - Parameters and their meaning
  - Return value
  - Exceptions that may be raised
- Use auto-generated API documentation (e.g., Swagger/OpenAPI for web endpoints, Sphinx for Python, DocFX for C#).
- Inline comments only for *why* something is done, not *what* the code does (the code should be self-explanatory).

## 16. Minimum Supported Languages / Runtimes

For any new production service, the team must choose from the following approved stacks:

| Layer | Approved Options |
|---|---|
| Backend | Python (3.10+), C# (.NET 8+) |
| Frontend | TypeScript + React / Vue 3 (no new jQuery projects) |
| Database | PostgreSQL, SQL Server, SQLite (for edge/embedded) |
| Infrastructure | Docker + docker-compose for local dev; CI/CD via GitHub Actions / Azure Pipelines |

Legacy jQuery code may be maintained but must not be expanded.
