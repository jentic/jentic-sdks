"""Tests for SearchResult handling of the new WorkflowSearchResult format.

The server-side WorkflowSearchResult now carries ``api_references`` instead
of a single ``api_name`` string.  These tests verify that the client-side
SearchResult model correctly derives ``api_name`` for backward compatibility
and preserves the full ``api_references`` list.
"""

import pytest

from jentic.lib.models import (
    APIReferenceSummary,
    SearchResult,
    SearchResponse,
    _derive_api_name,
)


# ---------------------------------------------------------------------------
# _derive_api_name helper
# ---------------------------------------------------------------------------

class TestDeriveApiName:
    def test_explicit_api_name_wins(self):
        data = {"api_name": "discord.com", "api_references": [{"api_name": "other"}]}
        assert _derive_api_name(data) == "discord.com"

    def test_falls_back_to_api_references(self):
        data = {
            "api_references": [
                {"api_id": "a1", "api_name": "discord.com", "api_version": "10"},
            ]
        }
        assert _derive_api_name(data) == "discord.com"

    def test_first_reference_used_when_multiple(self):
        data = {
            "api_references": [
                {"api_id": "a1", "api_name": "discord.com", "api_version": "10"},
                {"api_id": "a2", "api_name": "slack.com", "api_version": "2"},
            ]
        }
        assert _derive_api_name(data) == "discord.com"

    def test_empty_api_references(self):
        assert _derive_api_name({"api_references": []}) == ""

    def test_no_api_name_and_no_references(self):
        assert _derive_api_name({}) == ""

    def test_none_api_name_falls_back(self):
        data = {
            "api_name": None,
            "api_references": [{"api_name": "fallback.com"}],
        }
        assert _derive_api_name(data) == "fallback.com"

    def test_empty_string_api_name_falls_back(self):
        data = {
            "api_name": "",
            "api_references": [{"api_name": "fallback.com"}],
        }
        assert _derive_api_name(data) == "fallback.com"

    def test_api_references_with_model_objects(self):
        refs = [APIReferenceSummary(api_id="a1", api_name="hubspot.com", api_version="3")]
        data = {"api_references": refs}
        assert _derive_api_name(data) == "hubspot.com"


# ---------------------------------------------------------------------------
# SearchResult model — new workflow format (api_references, no api_name)
# ---------------------------------------------------------------------------

class TestSearchResultNewWorkflowFormat:
    """Validate SearchResult with the new WorkflowSearchResult payload."""

    def _workflow_payload(self, **overrides):
        base = {
            "id": "wf_abc123",
            "entity_type": "workflow",
            "name": "Send Discord Message",
            "workflow_id": "sendDiscordMessage",
            "description": "Send a message to a Discord channel",
            "distance": 0.12,
            "api_references": [
                {"api_id": "api_1", "api_name": "discord.com", "api_version": "10"},
            ],
        }
        base.update(overrides)
        return base

    def test_api_name_derived_from_references(self):
        result = SearchResult.model_validate(self._workflow_payload())
        assert result.api_name == "discord.com"

    def test_api_references_preserved(self):
        result = SearchResult.model_validate(self._workflow_payload())
        assert result.api_references is not None
        assert len(result.api_references) == 1
        assert result.api_references[0].api_name == "discord.com"

    def test_multi_api_references(self):
        payload = self._workflow_payload(
            api_references=[
                {"api_id": "a1", "api_name": "discord.com", "api_version": "10"},
                {"api_id": "a2", "api_name": "slack.com", "api_version": "2"},
            ]
        )
        result = SearchResult.model_validate(payload)
        assert result.api_name == "discord.com"
        assert len(result.api_references) == 2

    def test_no_api_references_yields_empty_name(self):
        payload = self._workflow_payload(api_references=None)
        result = SearchResult.model_validate(payload)
        assert result.api_name == ""
        assert result.api_references is None

    def test_workflow_id_preserved(self):
        result = SearchResult.model_validate(self._workflow_payload())
        assert result.workflow_id == "sendDiscordMessage"

    def test_name_used_as_summary(self):
        result = SearchResult.model_validate(self._workflow_payload())
        assert result.summary == "Send Discord Message"

    def test_match_score_from_distance(self):
        result = SearchResult.model_validate(self._workflow_payload())
        assert result.match_score == pytest.approx(0.12)

    def test_path_and_method_empty_for_workflow(self):
        result = SearchResult.model_validate(self._workflow_payload())
        assert result.path == ""
        assert result.method == ""


# ---------------------------------------------------------------------------
# SearchResult model — legacy format (top-level api_name, no api_references)
# ---------------------------------------------------------------------------

class TestSearchResultLegacyFormat:
    """Ensure backward compatibility with the old single-api_name format."""

    def _legacy_workflow_payload(self):
        return {
            "id": "wf_legacy",
            "entity_type": "workflow",
            "name": "Legacy Workflow",
            "workflow_id": "legacyWf",
            "description": "A legacy workflow",
            "api_name": "legacy-api.com",
            "distance": 0.5,
        }

    def test_api_name_preserved(self):
        result = SearchResult.model_validate(self._legacy_workflow_payload())
        assert result.api_name == "legacy-api.com"

    def test_api_references_none(self):
        result = SearchResult.model_validate(self._legacy_workflow_payload())
        assert result.api_references is None


class TestSearchResultOperationFormat:
    """Operations still carry top-level api_name — verify no regression."""

    def _operation_payload(self):
        return {
            "id": "op_xyz789",
            "entity_type": "operation",
            "summary": "Get user profile",
            "description": "Returns user profile data",
            "path": "/users/{id}",
            "method": "GET",
            "api_name": "github.com",
            "distance": 0.3,
            "operation_id": "getUserProfile",
        }

    def test_api_name(self):
        result = SearchResult.model_validate(self._operation_payload())
        assert result.api_name == "github.com"

    def test_operation_fields(self):
        result = SearchResult.model_validate(self._operation_payload())
        assert result.path == "/users/{id}"
        assert result.method == "GET"
        assert result.operation_id == "getUserProfile"
        assert result.summary == "Get user profile"


# ---------------------------------------------------------------------------
# SearchResponse — mixed results
# ---------------------------------------------------------------------------

class TestSearchResponseMixed:
    """Full response containing both new-format workflows and operations."""

    def test_validates_mixed_results(self):
        payload = {
            "results": [
                {
                    "id": "wf_1",
                    "entity_type": "workflow",
                    "name": "WF One",
                    "workflow_id": "wf1",
                    "description": "desc",
                    "distance": 0.1,
                    "api_references": [
                        {"api_id": "a1", "api_name": "discord.com", "api_version": "10"},
                    ],
                },
                {
                    "id": "op_1",
                    "entity_type": "operation",
                    "summary": "Op One",
                    "description": "desc",
                    "path": "/op",
                    "method": "POST",
                    "api_name": "slack.com",
                    "distance": 0.2,
                },
            ],
            "total_count": 2,
            "query": "send message",
        }
        resp = SearchResponse.model_validate(payload)
        assert len(resp.results) == 2

        wf = resp.results[0]
        assert wf.api_name == "discord.com"
        assert wf.api_references is not None

        op = resp.results[1]
        assert op.api_name == "slack.com"
        assert op.api_references is None


# ---------------------------------------------------------------------------
# APIReferenceSummary model
# ---------------------------------------------------------------------------

class TestAPIReferenceSummary:
    def test_basic_construction(self):
        ref = APIReferenceSummary(api_id="a1", api_name="test.com", api_version="1.0")
        assert ref.api_id == "a1"
        assert ref.api_name == "test.com"
        assert ref.api_version == "1.0"

    def test_defaults(self):
        ref = APIReferenceSummary()
        assert ref.api_id == ""
        assert ref.api_name == ""
        assert ref.api_version == ""

    def test_from_dict(self):
        ref = APIReferenceSummary.model_validate(
            {"api_id": "x", "api_name": "y", "api_version": "z"}
        )
        assert ref.api_name == "y"
