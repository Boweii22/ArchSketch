"""Detector for go.mod files (Go projects)."""

from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Map module path substrings to (tech_name, category)
TECH_PATTERNS = {
    # Web frameworks
    "gin-gonic/gin": ("Gin", TechCategory.BACKEND),
    "labstack/echo": ("Echo", TechCategory.BACKEND),
    "gofiber/fiber": ("Fiber", TechCategory.BACKEND),
    "gorilla/mux": ("Gorilla Mux", TechCategory.BACKEND),
    "go-chi/chi": ("Chi", TechCategory.BACKEND),
    "beego": ("Beego", TechCategory.BACKEND),
    "iris-go/iris": ("Iris", TechCategory.BACKEND),
    "go-resty/resty": ("Resty", TechCategory.BACKEND),
    "urfave/negroni": ("Negroni", TechCategory.BACKEND),
    "go-martini/martini": ("Martini", TechCategory.BACKEND),
    "net/http": ("Go net/http", TechCategory.BACKEND),
    "fasthttp": ("fasthttp", TechCategory.BACKEND),

    # Database / ORMs
    "gorm.io/gorm": ("GORM", TechCategory.DATABASE),
    "gorm.io/driver/postgres": ("PostgreSQL", TechCategory.DATABASE),
    "gorm.io/driver/mysql": ("MySQL", TechCategory.DATABASE),
    "gorm.io/driver/sqlite": ("SQLite", TechCategory.DATABASE),
    "lib/pq": ("PostgreSQL", TechCategory.DATABASE),
    "jackc/pgx": ("PostgreSQL", TechCategory.DATABASE),
    "go-sql-driver/mysql": ("MySQL", TechCategory.DATABASE),
    "mattn/go-sqlite3": ("SQLite", TechCategory.DATABASE),
    "mongo-driver": ("MongoDB", TechCategory.DATABASE),
    "uptrace/bun": ("Bun ORM", TechCategory.DATABASE),
    "jmoiron/sqlx": ("SQLx", TechCategory.DATABASE),

    # Cache
    "go-redis/redis": ("Redis", TechCategory.CACHE),
    "redis/go-redis": ("Redis", TechCategory.CACHE),
    "bradfitz/gomemcache": ("Memcached", TechCategory.CACHE),

    # Queue / messaging
    "streadway/amqp": ("RabbitMQ", TechCategory.QUEUE),
    "rabbitmq/amqp091-go": ("RabbitMQ", TechCategory.QUEUE),
    "confluentinc/confluent-kafka-go": ("Kafka", TechCategory.QUEUE),
    "segmentio/kafka-go": ("Kafka", TechCategory.QUEUE),
    "nats-io/nats.go": ("NATS", TechCategory.QUEUE),
    "nsqio/go-nsq": ("NSQ", TechCategory.QUEUE),
}


def detect_from_go_mod(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a go.mod file."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    detections.append(TechnologyDetection(
        source_file=source,
        tech="Go",
        category=TechCategory.BACKEND,
        confidence=0.95,
        details="go.mod found — Go project",
    ))

    detected_techs: set[str] = {"Go"}

    for line in content.splitlines():
        line = line.strip()
        # Dependency lines look like: github.com/gin-gonic/gin v1.9.1
        if not line or line.startswith("//") or line.startswith("module") or line.startswith("go "):
            continue
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pattern in line:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found '{pattern}' in go.mod",
                    ))

    return detections
