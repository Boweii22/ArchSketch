# ArchSketch

A Python CLI tool that scans any project directory and automatically infers its system architecture from common project files, then displays a beautiful ASCII diagram in your terminal.

**No configuration needed.** Just point it at a folder.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/archsketch.git
cd archsketch

# Set up Python environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install
pip install -e .

# Run on any project!
archsketch analyze /path/to/your/project
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
              |   [] Database  | |    <> Cache   |
              |   PostgreSQL   | |     Redis     |
              +----------------+ +----------------+

+------------------------ Legend -------------------------+
|  ## Frontend | @@ Backend | [] Database | <> Cache | >> Proxy |
+---------------------------------------------------------+
```

## Screenshots
<img width="1886" height="903" alt="image" src="https://github.com/user-attachments/assets/d3c7909b-f350-4a37-8786-cace590750ee" />
<img width="1917" height="1074" alt="image" src="https://github.com/user-attachments/assets/41fe360f-4b33-4e15-a96f-e86b3ce597bf" />

## Usage

### Analyze any project

```bash
archsketch analyze .                           # Current directory
archsketch analyze /path/to/your/project       # Any project folder
archsketch analyze ~/code/my-app               # Home directory path
archsketch analyze . --compact                 # Diagram only, no detections table
archsketch analyze . --no-table                # Same as --compact
```

### Export to Mermaid

```bash
archsketch export /path/to/project --format mermaid --output architecture.mmd
```

### Export to SVG (shareable image)

```bash
# Requires: pip install graphviz AND Graphviz binaries (https://graphviz.org/download/)
archsketch export . --format graphviz --output architecture.svg

# Or export DOT file (no binary needed), then convert: dot -Tsvg architecture.dot -o architecture.svg
archsketch export . --format dot --output architecture.dot
```

Generates:

```mermaid
graph TD
  frontend[Frontend: Next.js]
  backend[Backend: FastAPI]
  database[Database: PostgreSQL]
  cache[Cache: Redis]

  frontend --> backend
  backend --> database
  backend --> cache
```

### JSON output

```bash
archsketch analyze /path/to/project --json
```

### Show Mermaid in terminal

```bash
archsketch show /path/to/project
```

### Compare architecture between git refs (diff)

Requires: `pip install gitpython`

```bash
archsketch diff main feature-branch
archsketch diff HEAD~1 HEAD ./src
```

Shows added/removed components and edges (e.g. `+ Cache: Redis`, `- Database: MySQL`).

### Explain in the diagram

- **ASCII**: Each node box shows a short "From: ..." source line when available.
- **Mermaid**: Comments in the `.mmd` file document which file each node came from.
- **JSON**: Each node has `sources` and `explanation` for CI/scripting.

### Stable JSON for CI

Export includes `$schema`, `version`, and consistent shape. Schema: `schema/architecture.json`.

```bash
archsketch analyze . --output architecture.json
```

## What It Detects

ArchSketch reads these files to understand your stack:

| File | What it detects |
|------|----------------|
| `package.json` | React, Next.js, Vue, Express, NestJS, Prisma, Redis, Remix, Astro, Hono, Supabase |
| `requirements.txt` | FastAPI, Flask, Django, Celery, psycopg2, redis, Supabase |
| `pyproject.toml` | Same as requirements.txt |
| `pom.xml` | Spring Boot, PostgreSQL, Redis, Kafka, Micronaut, Quarkus |
| `build.gradle` / `build.gradle.kts` | Spring Boot, PostgreSQL, Redis (Gradle) |
| `docker-compose.yml` | PostgreSQL, MySQL, Redis, Nginx, RabbitMQ, custom services |
| `Dockerfile` | Base images (node, python, nginx) |
| `.env` | Database URLs, Redis URLs, service connections |
| `nginx.conf` | Nginx, upstream backends, SSL, WebSocket |
| `Procfile` | web/worker process types, Gunicorn, Celery, Next.js |
| `deployment.yaml`, `service.yaml`, `k8s/*.yaml` | Kubernetes Deployments, Services, Ingress, container images |
| `*.tf` | Terraform (AWS RDS, Lambda, SQS, GCP, Azure resources) |

## Detected Technologies

| Role | Technologies |
|------|-------------|
| **Frontend** | React, Next.js, Vue.js, Nuxt.js, Angular, Svelte, **Remix**, **Astro**, **SolidJS**, **Qwik**, Preact |
| **Backend** | Express, NestJS, FastAPI, Flask, Django, Fastify, **Hono**, **Elysia**, **Spring Boot** (pom.xml), Micronaut, Quarkus |
| **Database** | PostgreSQL, MySQL, MongoDB, SQLite, **Supabase** |
| **Cache** | Redis, Memcached |
| **Reverse Proxy** | Nginx, Traefik, Caddy |
| **Worker** | Celery, Bull, RQ |
| **Queue** | RabbitMQ, Kafka |

## How It Works

```
Your Project          ArchSketch Pipeline              Output
    │                        │                           │
    ├─ package.json    ──►   │                           │
    ├─ requirements.txt ──►  │  1. Scan files            │
    ├─ docker-compose.yml ►  │  2. Detect technologies   │  ──► ASCII Diagram
    ├─ Dockerfile      ──►   │  3. Infer relationships   │  ──► Mermaid Export
    └─ .env            ──►   │  4. Build graph           │  ──► JSON Data
                             │  5. Render                 │
```

1. **Scanner** - Walks your project, finds architecture-related files
2. **Detectors** - Parse each file type, extract technology signals
3. **Inference Engine** - Apply rules to determine roles and connections
4. **Renderer** - Output as ASCII art or Mermaid diagram

## Try It On Popular Projects

```bash
# Clone any open source project and analyze it
git clone https://github.com/tiangolo/full-stack-fastapi-template
archsketch analyze full-stack-fastapi-template

# Or your own projects
archsketch analyze ~/code/my-saas-app
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
│   ├── main.py              # CLI commands
│   ├── scanner.py           # File discovery
│   ├── models.py            # Data structures
│   ├── detectors/           # Technology detection
│   │   ├── package_json.py
│   │   ├── requirements_txt.py
│   │   ├── docker_compose.py
│   │   └── dockerfile.py
│   ├── inference/
│   │   └── engine.py        # Architecture inference rules
│   └── renderers/
│       ├── ascii_renderer.py
│       └── mermaid_renderer.py
├── schema/
│   └── architecture.json   # JSON schema for export (CI/scripting)
├── tests/                  # 60+ tests
├── samples/                 # Example projects
└── pyproject.toml
```

## Requirements

- Python 3.9+
- No external services needed
- Works offline

## License

MIT
