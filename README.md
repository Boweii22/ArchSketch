# ArchSketch

A Python CLI tool that scans any project directory — or any public GitHub repository — and automatically infers its system architecture from project files, then displays a beautiful ASCII diagram in your terminal.

**No configuration needed.** Just point it at a folder or a GitHub URL.

## Install

```bash
pip install archsketch
```

## Quick Start

```bash
# Local project
archsketch analyze .
archsketch analyze /path/to/your/project

# Public GitHub repo — no cloning required
archsketch analyze tiangolo/fastapi
archsketch analyze https://github.com/rails/rails
```

## Example Output

```
                          ARCHITECTURE SKETCH

                    +--------------------------+
                    |     >> Reverse Proxy     |
                    |          Nginx           |
                    +--------------------------+
                                 |
                                 v
                    +--------------------------+
                    |       ## Frontend        |
                    |         Next.js          |
                    +--------------------------+
                                 |
                                 v
                    +--------------------------+
                    |       @@ Backend         |
                    |         FastAPI          |
                    +--------------------------+
                          |            |
                          v            v
              +----------------+ +----------------+
              |   [] Database  | |    <> Cache    |
              |   PostgreSQL   | |     Redis      |
              +----------------+ +----------------+

+------------------------ Legend -------------------------+
|  ## Frontend | @@ Backend | [] Database | <> Cache | >> Proxy |
+---------------------------------------------------------+
```

## Screenshots
### Terminal output (analyze)
<img width="1886" height="903" alt="image" src="https://github.com/user-attachments/assets/d3c7909b-f350-4a37-8786-cace590750ee" />

### Exported SVG
<img width="1917" height="1074" alt="image" src="https://github.com/user-attachments/assets/41fe360f-4b33-4e15-a96f-e86b3ce597bf" />

## Usage

### Analyze any project

```bash
archsketch analyze .                          # Current directory
archsketch analyze /path/to/your/project      # Local path
archsketch analyze tiangolo/fastapi           # GitHub owner/repo
archsketch analyze https://github.com/django/django  # Full GitHub URL
archsketch analyze rails/rails --clone        # Full clone instead of API fetch
archsketch analyze . --compact                # Diagram only, no detections table
archsketch analyze . --show-sources           # Show which file each node came from
```

#### GitHub targets

By default ArchSketch fetches only the architecture-relevant files from GitHub via the API — no `git` required, no full clone. If you need complete file coverage (e.g. unusual project layouts), add `--clone`:

```bash
archsketch analyze tiangolo/fastapi           # Fast: API fetch only (~5-15 files)
archsketch analyze tiangolo/fastapi --clone   # Full shallow clone
```

### Export to Mermaid

```bash
archsketch export . --format mermaid --output architecture.mmd
archsketch export tiangolo/fastapi --format mermaid --output fastapi.mmd
```

### Export to SVG

```bash
# Requires: pip install graphviz AND Graphviz binaries (https://graphviz.org/download/)
archsketch export . --format graphviz --output architecture.svg

# Or export DOT file (no binary needed)
archsketch export . --format dot --output architecture.dot
```

### Explain detection reasoning

```bash
archsketch explain .
archsketch explain rails/rails
```

### Show Mermaid in terminal

```bash
archsketch show .
archsketch show gin-gonic/gin
```

### JSON output (CI/scripting)

```bash
archsketch analyze . --json
archsketch analyze . --output architecture.json
```

### Compare architecture between git refs

Requires: `pip install gitpython`

```bash
archsketch diff main feature-branch
archsketch diff HEAD~1 HEAD ./src
```

Shows added/removed components and edges between two branches or commits.

## What It Detects

ArchSketch reads these files to understand your stack:

| File | Ecosystem | What it detects |
|------|-----------|----------------|
| `package.json` | Node.js | React, Next.js, Vue, Express, NestJS, Prisma, Redis, Remix, Astro, Hono, Supabase |
| `requirements.txt` / `pyproject.toml` | Python | FastAPI, Flask, Django, Celery, psycopg2, Redis, Supabase |
| `Cargo.toml` | Rust | Axum, Actix Web, Rocket, SQLx, Diesel, Redis, Kafka |
| `go.mod` | Go | Gin, Echo, Fiber, GORM, PostgreSQL, MongoDB, Redis, Kafka |
| `pom.xml` / `build.gradle` | Java | Spring Boot, PostgreSQL, Redis, Kafka, Micronaut, Quarkus |
| `*.csproj` / `*.fsproj` | C# / .NET | ASP.NET Core, Blazor, EF Core, PostgreSQL, Redis, MassTransit, Hangfire |
| `Gemfile` | Ruby | Rails, Sinatra, PostgreSQL, Redis, Sidekiq, RabbitMQ |
| `composer.json` | PHP | Laravel, Symfony, Slim, Doctrine ORM, Redis, RabbitMQ |
| `pubspec.yaml` | Dart / Flutter | Flutter, Firebase, SQLite, Supabase, Riverpod, Shelf |
| `mix.exs` | Elixir | Phoenix, Ecto, PostgreSQL, Redis, Oban, Broadway, Kafka |
| `Package.swift` | Swift | Vapor, Hummingbird, Fluent ORM, PostgreSQL, Redis |
| `CMakeLists.txt` / `Makefile` | C / C++ | Qt, SDL, Crow, Drogon, SQLite, PostgreSQL, Redis, Kafka |
| `docker-compose.yml` | Docker | PostgreSQL, MySQL, Redis, Nginx, RabbitMQ, Kafka |
| `Dockerfile` | Docker | Base images (node, python, nginx) |
| `.env` | Any | Database URLs, Redis URLs, service connections |
| `nginx.conf` | Nginx | Upstreams, SSL, WebSocket |
| `Procfile` | Heroku | web/worker process types, Gunicorn, Celery |
| `deployment.yaml` / `k8s/*.yaml` | Kubernetes | Deployments, Services, Ingress, container images |
| `*.tf` | Terraform | AWS RDS, Lambda, SQS, GCP, Azure resources |

If no config files are found, ArchSketch falls back to scanning source file extensions (`.rs`, `.go`, `.cs`, `.rb`, `.php`, `.dart`, `.ex`, `.swift`, `.c`, `.cpp`, `.java`, `.kt`, `.hs`, and more) to at least identify the language.

## Detected Technologies

| Role | Technologies |
|------|-------------|
| **Frontend** | React, Next.js, Vue.js, Nuxt.js, Angular, Svelte, Remix, Astro, SolidJS, Qwik, Preact, Flutter, Blazor |
| **Backend** | Express, NestJS, FastAPI, Flask, Django, Fastify, Hono, Elysia, Spring Boot, Axum, Actix Web, Rocket, Gin, Echo, Fiber, Rails, Laravel, Symfony, Phoenix, Vapor, ASP.NET Core |
| **Database** | PostgreSQL, MySQL, MongoDB, SQLite, Supabase, Firebase, Cosmos DB, DynamoDB |
| **Cache** | Redis, Memcached |
| **Reverse Proxy** | Nginx, Traefik, Caddy |
| **Worker** | Celery, Sidekiq, Oban, Hangfire, Delayed Job |
| **Queue** | RabbitMQ, Kafka, NATS, BullMQ, Azure Service Bus |

## How It Works

```
Your Project / GitHub Repo     ArchSketch Pipeline              Output
         │                             │                           │
         ├─ Cargo.toml          ──►    │                           │
         ├─ go.mod              ──►    │  1. Scan files            │
         ├─ package.json        ──►    │  2. Detect technologies   │  ──► ASCII Diagram
         ├─ docker-compose.yml  ──►    │  3. Infer relationships   │  ──► Mermaid Export
         ├─ requirements.txt    ──►    │  4. Build graph           │  ──► SVG / DOT
         └─ *.tf                ──►    │  5. Render                │  ──► JSON Data
```

1. **Scanner** — walks your project, finds architecture-related files
2. **Detectors** — parse each file type, extract technology signals with confidence scores
3. **Inference Engine** — applies rules to determine roles and connections
4. **Renderer** — outputs as ASCII art, Mermaid, SVG, or JSON

## Try It On Popular Projects

```bash
# Python
archsketch analyze tiangolo/fastapi
archsketch analyze django/django

# JavaScript
archsketch analyze vercel/next.js
archsketch analyze nestjs/nest

# Rust
archsketch analyze tokio-rs/axum

# Go
archsketch analyze gin-gonic/gin

# Ruby
archsketch analyze rails/rails

# PHP
archsketch analyze laravel/laravel

# Elixir
archsketch analyze phoenixframework/phoenix

# Full stack with Docker/K8s/Terraform
archsketch analyze tiangolo/full-stack-fastapi-template
```

## Development

### Run tests

```bash
pip install -e ".[dev]"
pytest
```

### Project structure

```
archsketch/
├── archsketch/
│   ├── main.py              # CLI commands + GitHub fetch logic
│   ├── scanner.py           # File discovery
│   ├── models.py            # Data structures
│   ├── detectors/           # Technology detection (one file per ecosystem)
│   │   ├── package_json.py
│   │   ├── requirements_txt.py
│   │   ├── cargo_toml.py
│   │   ├── go_mod.py
│   │   ├── csproj.py
│   │   ├── gemfile.py
│   │   ├── composer_json.py
│   │   ├── pubspec_yaml.py
│   │   ├── mix_exs.py
│   │   ├── package_swift.py
│   │   ├── cmake.py
│   │   ├── docker_compose.py
│   │   ├── dockerfile.py
│   │   ├── terraform.py
│   │   ├── kubernetes.py
│   │   └── extension_scanner.py   # Fallback: detects language from file extensions
│   ├── inference/
│   │   └── engine.py        # Architecture inference rules
│   └── renderers/
│       ├── ascii_renderer.py
│       ├── mermaid_renderer.py
│       └── graphviz_renderer.py
├── tests/                   # 174+ tests
├── samples/                 # Example projects
└── pyproject.toml
```

## Requirements

- Python 3.9+
- No external services needed
- Works offline (for local paths)
- No `git` required for GitHub analysis (uses GitHub API)

## Troubleshooting

**`archsketch` command not found after `pip install archsketch`**

On Windows, if Python's Scripts folder isn't on your PATH, use:

```bash
python -m archsketch analyze .
```

**GitHub API rate limit**

The GitHub API allows 60 unauthenticated requests per hour. If you hit the limit, wait a few minutes or use `--clone` instead:

```bash
archsketch analyze tiangolo/fastapi --clone
```

**Private repositories**

The API fetch only works for public repos. For private repos, clone locally first:

```bash
git clone https://github.com/your-org/private-repo
archsketch analyze private-repo
```

## License

MIT
