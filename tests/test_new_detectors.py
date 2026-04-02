"""Tests for the new ecosystem detectors added in the multi-language update."""

import tempfile
from pathlib import Path

import pytest

from archsketch.detectors.cargo_toml import detect_from_cargo_toml
from archsketch.detectors.go_mod import detect_from_go_mod
from archsketch.detectors.csproj import detect_from_csproj
from archsketch.detectors.gemfile import detect_from_gemfile
from archsketch.detectors.composer_json import detect_from_composer_json
from archsketch.detectors.pubspec_yaml import detect_from_pubspec_yaml
from archsketch.detectors.mix_exs import detect_from_mix_exs
from archsketch.detectors.package_swift import detect_from_package_swift
from archsketch.detectors.cmake import detect_from_cmake
from archsketch.models import TechCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp: str, name: str, content: str) -> Path:
    p = Path(tmp) / name
    p.write_text(content, encoding="utf-8")
    return p


def _techs(detections) -> set[str]:
    return {d.tech for d in detections}


def _categories(detections) -> set[str]:
    return {d.category for d in detections}


# ---------------------------------------------------------------------------
# Cargo.toml (Rust)
# ---------------------------------------------------------------------------

class TestCargoTomlDetector:

    def test_rust_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[package]\nname = "hello"\nversion = "0.1.0"\n')
            d = detect_from_cargo_toml(f)
            assert "Rust" in _techs(d)

    def test_rust_category_is_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[package]\nname = "x"\n')
            d = detect_from_cargo_toml(f)
            rust = next(x for x in d if x.tech == "Rust")
            assert rust.category == TechCategory.BACKEND

    def test_detect_axum(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\naxum = "0.7"\ntokio = "1"\n')
            assert "Axum" in _techs(detect_from_cargo_toml(f))

    def test_detect_actix_web(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nactix-web = "4"\n')
            assert "Actix Web" in _techs(detect_from_cargo_toml(f))

    def test_detect_actix_web_underscore(self):
        """actix_web (underscore variant) should also be detected."""
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nactix_web = "4"\n')
            assert "Actix Web" in _techs(detect_from_cargo_toml(f))

    def test_detect_rocket(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nrocket = "0.5"\n')
            assert "Rocket" in _techs(detect_from_cargo_toml(f))

    def test_detect_sqlx(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nsqlx = "0.7"\n')
            d = detect_from_cargo_toml(f)
            assert "SQLx" in _techs(d)
            sql = next(x for x in d if x.tech == "SQLx")
            assert sql.category == TechCategory.DATABASE

    def test_detect_diesel(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\ndiesel = "2"\n')
            assert "Diesel ORM" in _techs(detect_from_cargo_toml(f))

    def test_detect_redis(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nredis = "0.24"\n')
            d = detect_from_cargo_toml(f)
            assert "Redis" in _techs(d)
            r = next(x for x in d if x.tech == "Redis")
            assert r.category == TechCategory.CACHE

    def test_detect_mongodb(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nmongodb = "2.8"\n')
            assert "MongoDB" in _techs(detect_from_cargo_toml(f))

    def test_detect_kafka(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nrdkafka = "0.36"\n')
            d = detect_from_cargo_toml(f)
            assert "Kafka" in _techs(d)
            k = next(x for x in d if x.tech == "Kafka")
            assert k.category == TechCategory.QUEUE

    def test_detect_multiple_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", (
                "[dependencies]\naxum = \"0.7\"\nsqlx = \"0.7\"\nredis = \"0.24\"\n"
            ))
            techs = _techs(detect_from_cargo_toml(f))
            assert {"Rust", "Axum", "SQLx", "Redis"}.issubset(techs)

    def test_no_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\nredis = "0.24"\ndeadpool-redis = "0.12"\n')
            d = detect_from_cargo_toml(f)
            redis_hits = [x for x in d if x.tech == "Redis"]
            assert len(redis_hits) == 1

    def test_invalid_file_returns_empty(self):
        assert detect_from_cargo_toml(Path("/nonexistent/Cargo.toml")) == []

    def test_confidence_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Cargo.toml", '[dependencies]\naxum = "0.7"\n')
            d = detect_from_cargo_toml(f)
            assert all(x.confidence >= 0.85 for x in d)


# ---------------------------------------------------------------------------
# go.mod (Go)
# ---------------------------------------------------------------------------

class TestGoModDetector:

    def test_go_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", "module github.com/example/app\n\ngo 1.21\n")
            assert "Go" in _techs(detect_from_go_mod(f))

    def test_go_category_is_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", "module example.com/app\ngo 1.21\n")
            d = detect_from_go_mod(f)
            go = next(x for x in d if x.tech == "Go")
            assert go.category == TechCategory.BACKEND

    def test_detect_gin(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgithub.com/gin-gonic/gin v1.9.1\n)\n"
            ))
            assert "Gin" in _techs(detect_from_go_mod(f))

    def test_detect_echo(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgithub.com/labstack/echo/v4 v4.11.0\n)\n"
            ))
            assert "Echo" in _techs(detect_from_go_mod(f))

    def test_detect_fiber(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgithub.com/gofiber/fiber/v2 v2.51.0\n)\n"
            ))
            assert "Fiber" in _techs(detect_from_go_mod(f))

    def test_detect_gorm_postgres(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgorm.io/gorm v1.25.0\n"
                "\tgorm.io/driver/postgres v1.5.0\n)\n"
            ))
            techs = _techs(detect_from_go_mod(f))
            assert "GORM" in techs
            assert "PostgreSQL" in techs

    def test_detect_redis(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgithub.com/go-redis/redis/v9 v9.0.0\n)\n"
            ))
            d = detect_from_go_mod(f)
            assert "Redis" in _techs(d)
            r = next(x for x in d if x.tech == "Redis")
            assert r.category == TechCategory.CACHE

    def test_detect_mongo(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgo.mongodb.org/mongo-driver v1.12.0\n)\n"
            ))
            assert "MongoDB" in _techs(detect_from_go_mod(f))

    def test_detect_kafka(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgithub.com/segmentio/kafka-go v0.4.44\n)\n"
            ))
            d = detect_from_go_mod(f)
            assert "Kafka" in _techs(d)
            k = next(x for x in d if x.tech == "Kafka")
            assert k.category == TechCategory.QUEUE

    def test_detect_rabbitmq(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "go.mod", (
                "module example.com/app\ngo 1.21\nrequire (\n"
                "\tgithub.com/rabbitmq/amqp091-go v1.9.0\n)\n"
            ))
            assert "RabbitMQ" in _techs(detect_from_go_mod(f))

    def test_invalid_file_returns_empty(self):
        assert detect_from_go_mod(Path("/nonexistent/go.mod")) == []


# ---------------------------------------------------------------------------
# .csproj (C# / .NET)
# ---------------------------------------------------------------------------

class TestCsprojDetector:

    def test_csharp_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "MyApp.csproj", "<Project Sdk=\"Microsoft.NET.Sdk\"></Project>")
            assert "C#" in _techs(detect_from_csproj(f))

    def test_fsharp_detected_from_fsproj(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "MyLib.fsproj", "<Project Sdk=\"Microsoft.NET.Sdk\"></Project>")
            assert "F#" in _techs(detect_from_csproj(f))

    def test_detect_aspnetcore(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "App.csproj", (
                '<Project>\n'
                '  <ItemGroup>\n'
                '    <PackageReference Include="Microsoft.AspNetCore.App" />\n'
                '  </ItemGroup>\n'
                '</Project>\n'
            ))
            assert "ASP.NET Core" in _techs(detect_from_csproj(f))

    def test_detect_ef_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "App.csproj", (
                '<Project>\n'
                '  <ItemGroup>\n'
                '    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />\n'
                '  </ItemGroup>\n'
                '</Project>\n'
            ))
            assert "Entity Framework Core" in _techs(detect_from_csproj(f))

    def test_detect_npgsql_postgres(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "App.csproj", (
                '<Project>\n'
                '  <ItemGroup>\n'
                '    <PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="8.0.0" />\n'
                '  </ItemGroup>\n'
                '</Project>\n'
            ))
            d = detect_from_csproj(f)
            assert "PostgreSQL" in _techs(d)
            pg = next(x for x in d if x.tech == "PostgreSQL")
            assert pg.category == TechCategory.DATABASE

    def test_detect_redis(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "App.csproj", (
                '<Project>\n'
                '  <ItemGroup>\n'
                '    <PackageReference Include="StackExchange.Redis" Version="2.7.0" />\n'
                '  </ItemGroup>\n'
                '</Project>\n'
            ))
            d = detect_from_csproj(f)
            assert "Redis" in _techs(d)
            r = next(x for x in d if x.tech == "Redis")
            assert r.category == TechCategory.CACHE

    def test_detect_masstransit_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "App.csproj", (
                '<Project>\n'
                '  <ItemGroup>\n'
                '    <PackageReference Include="MassTransit" Version="8.1.0" />\n'
                '  </ItemGroup>\n'
                '</Project>\n'
            ))
            d = detect_from_csproj(f)
            assert "MassTransit" in _techs(d)
            mt = next(x for x in d if x.tech == "MassTransit")
            assert mt.category == TechCategory.QUEUE

    def test_detect_hangfire_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "App.csproj", (
                '<Project>\n'
                '  <ItemGroup>\n'
                '    <PackageReference Include="Hangfire.Core" Version="1.8.0" />\n'
                '  </ItemGroup>\n'
                '</Project>\n'
            ))
            d = detect_from_csproj(f)
            assert "Hangfire" in _techs(d)
            h = next(x for x in d if x.tech == "Hangfire")
            assert h.category == TechCategory.WORKER

    def test_detect_blazor_frontend(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "App.csproj", (
                '<Project>\n'
                '  <ItemGroup>\n'
                '    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly" />\n'
                '  </ItemGroup>\n'
                '</Project>\n'
            ))
            d = detect_from_csproj(f)
            assert "Blazor WASM" in _techs(d)
            b = next(x for x in d if x.tech == "Blazor WASM")
            assert b.category == TechCategory.FRONTEND

    def test_invalid_file_returns_empty(self):
        assert detect_from_csproj(Path("/nonexistent/App.csproj")) == []


# ---------------------------------------------------------------------------
# Gemfile (Ruby)
# ---------------------------------------------------------------------------

class TestGemfileDetector:

    def test_ruby_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\n")
            assert "Ruby" in _techs(detect_from_gemfile(f))

    def test_ruby_category_is_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\n")
            d = detect_from_gemfile(f)
            ruby = next(x for x in d if x.tech == "Ruby")
            assert ruby.category == TechCategory.BACKEND

    def test_detect_rails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\ngem 'rails', '~> 7.1'\n")
            assert "Ruby on Rails" in _techs(detect_from_gemfile(f))

    def test_detect_sinatra(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\ngem 'sinatra'\n")
            assert "Sinatra" in _techs(detect_from_gemfile(f))

    def test_detect_postgres(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\ngem 'pg'\n")
            d = detect_from_gemfile(f)
            assert "PostgreSQL" in _techs(d)
            pg = next(x for x in d if x.tech == "PostgreSQL")
            assert pg.category == TechCategory.DATABASE

    def test_detect_mysql(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\ngem 'mysql2'\n")
            assert "MySQL" in _techs(detect_from_gemfile(f))

    def test_detect_redis(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\ngem 'redis'\n")
            d = detect_from_gemfile(f)
            assert "Redis" in _techs(d)
            r = next(x for x in d if x.tech == "Redis")
            assert r.category == TechCategory.CACHE

    def test_detect_sidekiq(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\ngem 'sidekiq'\n")
            d = detect_from_gemfile(f)
            assert "Sidekiq" in _techs(d)
            s = next(x for x in d if x.tech == "Sidekiq")
            assert s.category == TechCategory.WORKER

    def test_detect_double_quoted_gems(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", 'source "https://rubygems.org"\ngem "rails", "~> 7.1"\n')
            assert "Ruby on Rails" in _techs(detect_from_gemfile(f))

    def test_detect_rabbitmq_bunny(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Gemfile", "source 'https://rubygems.org'\ngem 'bunny'\n")
            d = detect_from_gemfile(f)
            assert "RabbitMQ" in _techs(d)
            r = next(x for x in d if x.tech == "RabbitMQ")
            assert r.category == TechCategory.QUEUE

    def test_invalid_file_returns_empty(self):
        assert detect_from_gemfile(Path("/nonexistent/Gemfile")) == []


# ---------------------------------------------------------------------------
# composer.json (PHP)
# ---------------------------------------------------------------------------

class TestComposerJsonDetector:

    def test_php_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"name": "my/app", "require": {}}')
            assert "PHP" in _techs(detect_from_composer_json(f))

    def test_detect_laravel(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"require": {"laravel/framework": "^10.0"}}')
            assert "Laravel" in _techs(detect_from_composer_json(f))

    def test_detect_symfony(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"require": {"symfony/framework-bundle": "^6.4"}}')
            assert "Symfony" in _techs(detect_from_composer_json(f))

    def test_detect_slim(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"require": {"slim/slim": "^4.0"}}')
            assert "Slim" in _techs(detect_from_composer_json(f))

    def test_detect_doctrine_orm(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"require": {"doctrine/orm": "^3.0"}}')
            d = detect_from_composer_json(f)
            assert "Doctrine ORM" in _techs(d)
            o = next(x for x in d if x.tech == "Doctrine ORM")
            assert o.category == TechCategory.DATABASE

    def test_detect_redis_predis(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"require": {"predis/predis": "^2.0"}}')
            d = detect_from_composer_json(f)
            assert "Redis" in _techs(d)
            r = next(x for x in d if x.tech == "Redis")
            assert r.category == TechCategory.CACHE

    def test_detect_rabbitmq(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"require": {"php-amqplib/php-amqplib": "^3.0"}}')
            d = detect_from_composer_json(f)
            assert "RabbitMQ" in _techs(d)

    def test_detect_from_require_dev(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", '{"require-dev": {"laravel/framework": "^10.0"}}')
            assert "Laravel" in _techs(detect_from_composer_json(f))

    def test_invalid_json_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "composer.json", "not valid json {{{")
            assert detect_from_composer_json(f) == []

    def test_invalid_file_returns_empty(self):
        assert detect_from_composer_json(Path("/nonexistent/composer.json")) == []


# ---------------------------------------------------------------------------
# pubspec.yaml (Dart / Flutter)
# ---------------------------------------------------------------------------

class TestPubspecYamlDetector:

    def test_dart_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "pubspec.yaml", "name: my_app\nversion: 1.0.0\n")
            assert "Dart" in _techs(detect_from_pubspec_yaml(f))

    def test_detect_flutter(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "pubspec.yaml", (
                "name: my_app\ndependencies:\n  flutter:\n    sdk: flutter\n"
            ))
            d = detect_from_pubspec_yaml(f)
            assert "Flutter" in _techs(d)
            fl = next(x for x in d if x.tech == "Flutter")
            assert fl.category == TechCategory.FRONTEND

    def test_detect_firebase(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "pubspec.yaml", (
                "name: my_app\ndependencies:\n  firebase_core: ^2.24.0\n"
            ))
            d = detect_from_pubspec_yaml(f)
            assert "Firebase" in _techs(d)
            fb = next(x for x in d if x.tech == "Firebase")
            assert fb.category == TechCategory.DATABASE

    def test_detect_sqflite(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "pubspec.yaml", (
                "name: my_app\ndependencies:\n  sqflite: ^2.3.0\n"
            ))
            d = detect_from_pubspec_yaml(f)
            assert "SQLite" in _techs(d)

    def test_detect_supabase(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "pubspec.yaml", (
                "name: my_app\ndependencies:\n  supabase_flutter: ^2.0.0\n"
            ))
            assert "Supabase" in _techs(detect_from_pubspec_yaml(f))

    def test_detect_riverpod(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "pubspec.yaml", (
                "name: my_app\ndependencies:\n  flutter_riverpod: ^2.4.0\n"
            ))
            assert "Riverpod" in _techs(detect_from_pubspec_yaml(f))

    def test_detect_shelf_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "pubspec.yaml", (
                "name: my_server\ndependencies:\n  shelf: ^1.4.0\n"
            ))
            d = detect_from_pubspec_yaml(f)
            assert "Shelf" in _techs(d)
            s = next(x for x in d if x.tech == "Shelf")
            assert s.category == TechCategory.BACKEND

    def test_invalid_file_returns_empty(self):
        assert detect_from_pubspec_yaml(Path("/nonexistent/pubspec.yaml")) == []


# ---------------------------------------------------------------------------
# mix.exs (Elixir)
# ---------------------------------------------------------------------------

class TestMixExsDetector:

    def test_elixir_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "mix.exs", (
                'defmodule MyApp.MixProject do\n'
                '  use Mix.Project\n'
                'end\n'
            ))
            assert "Elixir" in _techs(detect_from_mix_exs(f))

    def test_detect_phoenix(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "mix.exs", (
                'defmodule MyApp.MixProject do\n'
                '  defp deps do\n'
                '    [{:phoenix, "~> 1.7"}]\n'
                '  end\n'
                'end\n'
            ))
            assert "Phoenix" in _techs(detect_from_mix_exs(f))

    def test_detect_ecto_postgres(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "mix.exs", (
                'defmodule MyApp.MixProject do\n'
                '  defp deps do\n'
                '    [\n'
                '      {:ecto_sql, "~> 3.10"},\n'
                '      {:postgrex, ">= 0.0.0"}\n'
                '    ]\n'
                '  end\n'
                'end\n'
            ))
            techs = _techs(detect_from_mix_exs(f))
            assert "Ecto SQL" in techs
            assert "PostgreSQL" in techs

    def test_detect_redis_redix(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "mix.exs", (
                'defmodule MyApp.MixProject do\n'
                '  defp deps do\n'
                '    [{:redix, "~> 1.2"}]\n'
                '  end\n'
                'end\n'
            ))
            d = detect_from_mix_exs(f)
            assert "Redis" in _techs(d)
            r = next(x for x in d if x.tech == "Redis")
            assert r.category == TechCategory.CACHE

    def test_detect_oban_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "mix.exs", (
                'defmodule MyApp.MixProject do\n'
                '  defp deps do\n'
                '    [{:oban, "~> 2.17"}]\n'
                '  end\n'
                'end\n'
            ))
            d = detect_from_mix_exs(f)
            assert "Oban" in _techs(d)
            o = next(x for x in d if x.tech == "Oban")
            assert o.category == TechCategory.WORKER

    def test_detect_broadway_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "mix.exs", (
                'defmodule MyApp.MixProject do\n'
                '  defp deps do\n'
                '    [{:broadway, "~> 1.0"}]\n'
                '  end\n'
                'end\n'
            ))
            d = detect_from_mix_exs(f)
            assert "Broadway" in _techs(d)
            b = next(x for x in d if x.tech == "Broadway")
            assert b.category == TechCategory.QUEUE

    def test_detect_absinthe_graphql(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "mix.exs", (
                'defp deps do\n'
                '  [{:absinthe, "~> 1.7"}]\n'
                'end\n'
            ))
            assert "Absinthe (GraphQL)" in _techs(detect_from_mix_exs(f))

    def test_invalid_file_returns_empty(self):
        assert detect_from_mix_exs(Path("/nonexistent/mix.exs")) == []


# ---------------------------------------------------------------------------
# Package.swift (Swift)
# ---------------------------------------------------------------------------

class TestPackageSwiftDetector:

    def test_swift_always_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Package.swift", (
                '// swift-tools-version:5.9\nimport PackageDescription\n'
            ))
            assert "Swift" in _techs(detect_from_package_swift(f))

    def test_detect_vapor(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Package.swift", (
                '// swift-tools-version:5.9\n'
                'let package = Package(\n'
                '  dependencies: [\n'
                '    .package(url: "https://github.com/vapor/vapor.git", from: "4.0.0"),\n'
                '  ]\n'
                ')\n'
            ))
            d = detect_from_package_swift(f)
            assert "Vapor" in _techs(d)
            v = next(x for x in d if x.tech == "Vapor")
            assert v.category == TechCategory.BACKEND

    def test_detect_fluent_postgres(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Package.swift", (
                '// swift-tools-version:5.9\n'
                'let package = Package(\n'
                '  dependencies: [\n'
                '    .package(url: "https://github.com/vapor/fluent-postgres-driver.git", from: "2.0.0"),\n'
                '  ]\n'
                ')\n'
            ))
            d = detect_from_package_swift(f)
            assert "PostgreSQL" in _techs(d)
            pg = next(x for x in d if x.tech == "PostgreSQL")
            assert pg.category == TechCategory.DATABASE

    def test_detect_fluent_orm(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Package.swift", (
                '// swift-tools-version:5.9\n'
                'let package = Package(\n'
                '  dependencies: [\n'
                '    .package(url: "https://github.com/vapor/fluent.git", from: "4.0.0"),\n'
                '  ]\n'
                ')\n'
            ))
            assert "Fluent ORM" in _techs(detect_from_package_swift(f))

    def test_invalid_file_returns_empty(self):
        assert detect_from_package_swift(Path("/nonexistent/Package.swift")) == []


# ---------------------------------------------------------------------------
# CMakeLists.txt / Makefile (C / C++)
# ---------------------------------------------------------------------------

class TestCMakeDetector:

    def test_cpp_detected_from_cmakelists(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "CMakeLists.txt", (
                "cmake_minimum_required(VERSION 3.20)\n"
                "project(MyApp CXX)\n"
            ))
            d = detect_from_cmake(f)
            assert "C++" in _techs(d)

    def test_c_detected_from_makefile(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "Makefile", (
                "CC=gcc\nall: main.o\nmain.o: main.c\n\t$(CC) -c main.c\n"
            ))
            d = detect_from_cmake(f)
            assert any(t in _techs(d) for t in ("C", "C++", "C/C++"))

    def test_detect_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "CMakeLists.txt", (
                "cmake_minimum_required(VERSION 3.20)\n"
                "find_package(SQLite3 REQUIRED)\n"
            ))
            d = detect_from_cmake(f)
            assert "SQLite" in _techs(d)
            s = next(x for x in d if x.tech == "SQLite")
            assert s.category == TechCategory.DATABASE

    def test_detect_postgres_libpq(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "CMakeLists.txt", (
                "cmake_minimum_required(VERSION 3.20)\n"
                "target_link_libraries(app PRIVATE pqxx)\n"
            ))
            d = detect_from_cmake(f)
            assert "PostgreSQL" in _techs(d)

    def test_detect_qt_frontend(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "CMakeLists.txt", (
                "cmake_minimum_required(VERSION 3.20)\n"
                "find_package(Qt6 REQUIRED COMPONENTS Widgets)\n"
            ))
            d = detect_from_cmake(f)
            assert "Qt" in _techs(d)
            q = next(x for x in d if x.tech == "Qt")
            assert q.category == TechCategory.FRONTEND

    def test_detect_redis_hiredis(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "CMakeLists.txt", (
                "cmake_minimum_required(VERSION 3.20)\n"
                "find_package(hiredis REQUIRED)\n"
            ))
            d = detect_from_cmake(f)
            assert "Redis" in _techs(d)
            r = next(x for x in d if x.tech == "Redis")
            assert r.category == TechCategory.CACHE

    def test_detect_kafka(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "CMakeLists.txt", (
                "cmake_minimum_required(VERSION 3.20)\n"
                "find_package(RdKafka REQUIRED)\n"
            ))
            assert "Kafka" in _techs(detect_from_cmake(f))

    def test_confidence_is_reasonable(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _write(tmp, "CMakeLists.txt", "cmake_minimum_required(VERSION 3.20)\n")
            d = detect_from_cmake(f)
            assert all(x.confidence >= 0.5 for x in d)

    def test_invalid_file_returns_empty(self):
        assert detect_from_cmake(Path("/nonexistent/CMakeLists.txt")) == []
