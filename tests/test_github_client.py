import pytest
from unittest.mock import MagicMock, patch
import httpx
from src.tools.github_client import GitHubClient


def test_github_client_fallback_mode():
    client = GitHubClient(token="")
    assert not client.is_configured()

    pr_result = client.create_patch_pull_request(
        repo="backend/auth-service",
        branch="fix/auth-service-patch",
        title="fix(auth-service): null pointer",
        patch_content="Sample patch",
        incident_id="INC-101",
        service_slug="auth-service",
    )
    assert pr_result["status"] == "created"
    assert pr_result["simulated"] is True
    assert "https://github.com" in pr_result["pr_url"]
    assert pr_result["pr_number"] == 142

    issue_result = client.create_issue(
        repo="backend/auth-service",
        title="[SRE Prevention] Hardening",
        body="Action item",
        labels=["sre", "prevention"],
    )
    assert issue_result["status"] == "created"
    assert issue_result["simulated"] is True
    assert "https://github.com" in issue_result["issue_url"]


def test_github_client_resolve_repo():
    client = GitHubClient(token="mock_token", owner="GNOLIAHOV", default_repo="incident-response-agent")
    assert client.resolve_repo("custom-owner/target-repo") == "custom-owner/target-repo"
    # When relative service repo like backend/auth-service is passed, defaults to default_repo
    assert client.resolve_repo("backend/auth-service") == "GNOLIAHOV/incident-response-agent"
    assert client.resolve_repo("") == "GNOLIAHOV/incident-response-agent"


def test_github_client_live_mocked_success():
    client = GitHubClient(token="ghp_test_token_12345", owner="GNOLIAHOV", default_repo="incident-response-agent")
    assert client.is_configured()

    def mock_send(request: httpx.Request, **kwargs):
        url = str(request.url)
        if "/git/ref/heads/main" in url:
            return httpx.Response(200, json={"object": {"sha": "sha_base_123"}}, request=request)
        elif "/git/refs" in url:
            return httpx.Response(201, json={"ref": "refs/heads/fix/auth-patch"}, request=request)
        elif "/contents/incidents/patches/" in url and request.method == "GET":
            return httpx.Response(404, json={"message": "Not Found"}, request=request)
        elif "/contents/incidents/patches/" in url and request.method == "PUT":
            return httpx.Response(201, json={"content": {"path": "incidents/patches/INC-101-auth.md"}}, request=request)
        elif "/pulls" in url and request.method == "POST":
            return httpx.Response(201, json={"number": 42, "html_url": "https://github.com/GNOLIAHOV/incident-response-agent/pull/42"}, request=request)
        elif "/issues" in url and request.method == "POST":
            return httpx.Response(201, json={"number": 99, "html_url": "https://github.com/GNOLIAHOV/incident-response-agent/issues/99"}, request=request)
        return httpx.Response(404, json={"message": "Unhandled URL"}, request=request)

    with patch.object(httpx.Client, "send", side_effect=mock_send):
        pr_res = client.create_patch_pull_request(
            repo="backend/auth-service",
            branch="fix/auth-patch",
            title="fix(auth): fix token validation",
            patch_content="# Patch content",
            incident_id="INC-101",
            service_slug="auth-service",
        )
        assert pr_res["status"] == "created"
        assert pr_res["simulated"] is False
        assert pr_res["pr_number"] == 42
        assert pr_res["pr_url"] == "https://github.com/GNOLIAHOV/incident-response-agent/pull/42"

        issue_res = client.create_issue(
            repo="backend/auth-service",
            title="[SRE Prevention] Token hardening",
            body="Follow up on INC-101",
            labels=["sre", "prevention"],
        )
        assert issue_res["status"] == "created"
        assert issue_res["simulated"] is False
        assert issue_res["issue_number"] == 99


def test_github_client_live_mocked_existing_file_update():
    client = GitHubClient(token="ghp_test_token_12345", owner="GNOLIAHOV", default_repo="incident-response-agent")

    put_body = {}

    def mock_send(request: httpx.Request, **kwargs):
        url = str(request.url)
        if "/git/ref/heads/main" in url:
            return httpx.Response(200, json={"object": {"sha": "sha_base_123"}}, request=request)
        elif "/git/refs" in url:
            return httpx.Response(201, json={"ref": "refs/heads/fix/auth-patch"}, request=request)
        elif "/contents/incidents/patches/" in url and request.method == "GET":
            return httpx.Response(200, json={"sha": "existing_blob_sha_999"}, request=request)
        elif "/contents/incidents/patches/" in url and request.method == "PUT":
            import json
            put_body.update(json.loads(request.content.decode("utf-8")))
            return httpx.Response(200, json={"content": {"path": "incidents/patches/INC-101-auth.md"}}, request=request)
        elif "/pulls" in url and request.method == "POST":
            return httpx.Response(201, json={"number": 43, "html_url": "https://github.com/GNOLIAHOV/incident-response-agent/pull/43"}, request=request)
        return httpx.Response(404, json={"message": "Unhandled URL"}, request=request)

    with patch.object(httpx.Client, "send", side_effect=mock_send):
        pr_res = client.create_patch_pull_request(
            repo="backend/auth-service",
            branch="fix/auth-patch",
            title="fix(auth): update token patch",
            patch_content="# Updated patch",
            incident_id="INC-101",
            service_slug="auth-service",
        )
        assert pr_res["status"] == "created"
        assert pr_res["pr_number"] == 43
        assert put_body.get("sha") == "existing_blob_sha_999"


def test_github_client_live_exception_fallback():
    client = GitHubClient(token="ghp_invalid_token", owner="GNOLIAHOV", default_repo="incident-response-agent")

    def mock_send_error(request: httpx.Request, **kwargs):
        raise httpx.ConnectTimeout("Connection to GitHub timed out")

    with patch.object(httpx.Client, "send", side_effect=mock_send_error):
        pr_res = client.create_patch_pull_request(
            repo="backend/auth-service",
            branch="fix/auth-patch",
            title="fix(auth): timeout test",
            patch_content="# Content",
            incident_id="INC-TIMEOUT",
            service_slug="auth-service",
        )
        assert pr_res["status"] == "created"
        assert pr_res["simulated"] is True
        assert "GNOLIAHOV/incident-response-agent" in pr_res["pr_url"]
        assert "(URL: " in pr_res["message"]

        issue_res = client.create_issue(
            repo="backend/auth-service",
            title="[SRE Prevention] Timeout issue",
            body="Timeout body",
            labels=["sre"],
        )
        assert issue_res["status"] == "created"
        assert issue_res["simulated"] is True
