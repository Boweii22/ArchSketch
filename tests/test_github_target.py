"""Tests for GitHub URL parsing and the _should_fetch helper."""

import pytest

from archsketch.main import _parse_github_target, _should_fetch


# ---------------------------------------------------------------------------
# _parse_github_target
# ---------------------------------------------------------------------------

class TestParseGithubTarget:

    # --- valid inputs that should be recognised ---

    def test_full_https_url(self):
        result = _parse_github_target("https://github.com/tiangolo/fastapi")
        assert result == ("tiangolo", "fastapi", "")

    def test_full_https_url_with_git_suffix(self):
        result = _parse_github_target("https://github.com/tiangolo/fastapi.git")
        assert result == ("tiangolo", "fastapi", "")

    def test_https_url_with_branch(self):
        result = _parse_github_target("https://github.com/tiangolo/fastapi/tree/main")
        assert result == ("tiangolo", "fastapi", "main")

    def test_https_url_with_feature_branch(self):
        result = _parse_github_target("https://github.com/org/repo/tree/feature/my-branch")
        assert result is not None
        owner, repo, ref = result
        assert owner == "org"
        assert repo == "repo"

    def test_url_without_scheme(self):
        result = _parse_github_target("github.com/django/django")
        assert result == ("django", "django", "")

    def test_owner_slash_repo_shorthand(self):
        result = _parse_github_target("rails/rails")
        assert result == ("rails", "rails", "")

    def test_owner_slash_repo_with_dots(self):
        result = _parse_github_target("owner/repo.name")
        assert result is not None
        assert result[0] == "owner"
        assert result[1] == "repo.name"

    def test_owner_slash_repo_with_dashes(self):
        result = _parse_github_target("my-org/my-repo")
        assert result == ("my-org", "my-repo", "")

    def test_owner_slash_repo_with_numbers(self):
        result = _parse_github_target("user123/repo456")
        assert result == ("user123", "repo456", "")

    # --- inputs that should NOT be recognised as GitHub ---

    def test_local_absolute_path_unix(self):
        assert _parse_github_target("/home/user/projects/myapp") is None

    def test_local_relative_path(self):
        assert _parse_github_target("./myproject") is None

    def test_dot_current_dir(self):
        assert _parse_github_target(".") is None

    def test_windows_path(self):
        assert _parse_github_target(r"C:\Users\user\project") is None

    def test_just_a_name(self):
        assert _parse_github_target("myproject") is None

    def test_three_part_path_not_github(self):
        assert _parse_github_target("one/two/three") is None

    def test_empty_string(self):
        assert _parse_github_target("") is None

    def test_gitlab_url_not_matched(self):
        assert _parse_github_target("https://gitlab.com/user/repo") is None

    def test_bitbucket_url_not_matched(self):
        assert _parse_github_target("https://bitbucket.org/user/repo") is None

    # --- ref extraction ---

    def test_ref_is_empty_string_when_no_branch(self):
        owner, repo, ref = _parse_github_target("tiangolo/fastapi")
        assert ref == ""

    def test_ref_extracted_from_tree_url(self):
        owner, repo, ref = _parse_github_target("https://github.com/org/repo/tree/develop")
        assert ref == "develop"


# ---------------------------------------------------------------------------
# _should_fetch
# ---------------------------------------------------------------------------

class TestShouldFetch:

    # --- exact name matches ---

    def test_package_json(self):
        assert _should_fetch("package.json") is True

    def test_nested_package_json(self):
        assert _should_fetch("apps/web/package.json") is True

    def test_requirements_txt(self):
        assert _should_fetch("requirements.txt") is True

    def test_pyproject_toml(self):
        assert _should_fetch("pyproject.toml") is True

    def test_cargo_toml(self):
        assert _should_fetch("Cargo.toml") is True

    def test_go_mod(self):
        assert _should_fetch("go.mod") is True

    def test_gemfile(self):
        assert _should_fetch("Gemfile") is True

    def test_composer_json(self):
        assert _should_fetch("composer.json") is True

    def test_pubspec_yaml(self):
        assert _should_fetch("pubspec.yaml") is True

    def test_mix_exs(self):
        assert _should_fetch("mix.exs") is True

    def test_package_swift(self):
        assert _should_fetch("Package.swift") is True

    def test_cmakelists(self):
        assert _should_fetch("CMakeLists.txt") is True

    def test_makefile(self):
        assert _should_fetch("Makefile") is True

    def test_pom_xml(self):
        assert _should_fetch("pom.xml") is True

    def test_build_gradle(self):
        assert _should_fetch("build.gradle") is True

    def test_nginx_conf(self):
        assert _should_fetch("nginx.conf") is True

    def test_procfile(self):
        assert _should_fetch("Procfile") is True

    def test_dockerfile(self):
        assert _should_fetch("Dockerfile") is True

    def test_dockerfile_prod_variant(self):
        assert _should_fetch("Dockerfile.prod") is True

    def test_dockerfile_dev_variant(self):
        assert _should_fetch("Dockerfile.dev") is True

    def test_docker_compose_yml(self):
        assert _should_fetch("docker-compose.yml") is True

    def test_docker_compose_yaml(self):
        assert _should_fetch("docker-compose.yaml") is True

    def test_docker_compose_prod(self):
        assert _should_fetch("docker-compose.prod.yml") is True

    def test_env_file(self):
        assert _should_fetch(".env") is True

    def test_env_local(self):
        assert _should_fetch(".env.local") is True

    def test_env_example(self):
        assert _should_fetch(".env.example") is True

    def test_terraform_tf(self):
        assert _should_fetch("main.tf") is True

    def test_terraform_nested(self):
        assert _should_fetch("infra/aws/main.tf") is True

    def test_csproj(self):
        assert _should_fetch("MyApp.csproj") is True

    def test_fsproj(self):
        assert _should_fetch("MyLib.fsproj") is True

    def test_vbproj(self):
        assert _should_fetch("Legacy.vbproj") is True

    # --- kubernetes manifests ---

    def test_deployment_yaml(self):
        assert _should_fetch("deployment.yaml") is True

    def test_service_yaml(self):
        assert _should_fetch("service.yaml") is True

    def test_yaml_under_k8s_dir(self):
        assert _should_fetch("k8s/app.yaml") is True

    def test_yaml_under_kubernetes_dir(self):
        assert _should_fetch("kubernetes/postgres.yaml") is True

    # --- files that should NOT be fetched ---

    def test_readme_not_fetched(self):
        assert _should_fetch("README.md") is False

    def test_source_rs_not_fetched(self):
        assert _should_fetch("src/main.rs") is False

    def test_source_go_not_fetched(self):
        assert _should_fetch("main.go") is False

    def test_license_not_fetched(self):
        assert _should_fetch("LICENSE") is False

    def test_gitignore_not_fetched(self):
        assert _should_fetch(".gitignore") is False

    def test_random_yaml_not_fetched(self):
        assert _should_fetch("config/settings.yaml") is False

    def test_png_not_fetched(self):
        assert _should_fetch("logo.png") is False

    def test_test_file_not_fetched(self):
        assert _should_fetch("tests/test_app.py") is False
