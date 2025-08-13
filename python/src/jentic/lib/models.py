from typing import Any, Dict, cast

from pydantic import BaseModel, Field, model_validator


# Represents a reference to a file ID
class FileId(BaseModel):
    """Lightweight wrapper representing a file's unique identifier returned by the API Hub."""

    id: str = Field(..., description="Unique identifier of the file (UUID)")


# Represents the detailed file entry
class FileEntry(BaseModel):
    """
    Parameters
    ----------
    id :
        Unique identifier of the file on the API Hub.
    filename :
        Original filename as stored on the Hub.
    type :
        Logical file type (``open_api``, ``arazzo`` …) used to group files.
    content :
        Parsed JSON/YAML content of the file.
    source_path :
        Original path inside the vendor bundle. Present for Arazzo specs.
    """

    id: str = Field(..., description="Unique identifier of the file on the API Hub (UUID)")
    filename: str = Field(..., description="Original filename as uploaded to the Hub")
    type: str = Field(..., description="Logical file type category, e.g. 'open_api', 'arazzo'")
    content: dict[str, Any] = Field(
        default_factory=dict,
        description="Full parsed contents of the file (JSON object)",
    )
    source_path: str | None = Field(
        default=None,
        description="Original relative path inside the vendor bundle (if any)",
    )

    @model_validator(mode="before")
    @classmethod
    def handle_oak_path_alias(cls, values) -> Any:  # type: ignore[no-untyped-def]
        """Handle backward compatibility for oak_path field name."""
        if isinstance(values, dict):
            # If oak_path is provided but source_path is not, use oak_path
            if "oak_path" in values and "source_path" not in values:
                values["source_path"] = values.pop("oak_path")
            # If both are provided, prefer source_path and remove oak_path
            elif "oak_path" in values and "source_path" in values:
                values.pop("oak_path")
        return values

    @property
    def oak_path(self) -> str | None:
        """Backward compatibility property for oak_path."""
        return self.source_path


# Represents an API reference within a workflow
class APIReference(BaseModel):
    """Reference to an external API used inside a workflow definition."""

    api_id: str = Field(..., description="UUID of the referenced API")
    api_name: str = Field(..., description="Human-readable name of the API")
    api_version: str = Field(..., description="Version string of the referenced API")


class APIIdentifier(BaseModel):
    """Canonical identifier for an API as returned by :py:meth:`Jentic.list_apis`."""

    api_vendor: str = Field(..., description="Vendor domain, e.g. 'hubapi.com'")
    api_name: str | None = Field(
        default=None,
        description="API name (set when targeting a specific API; otherwise None)",
    )
    api_version: str | None = Field(
        default=None,
        description="Version string (set when targeting a specific version; otherwise None)",
    )


# Represents the spec info of an operation or workflow
class SpecInfo(BaseModel):
    """Metadata tuple identifying an OpenAPI specification or Arazzo bundle.

    This object is stored on each :class:`WorkflowEntry` / :class:`OperationEntry`
    so you can quickly tell which vendor and version a piece of spec data
    belongs to.
    """

    api_vendor: str = Field(..., description="Vendor domain, e.g. 'hubapi.com'")
    api_name: str = Field(..., description="Canonical API name inside the vendor")
    api_version: str | None = Field(
        default=None,
        description="Optional version string – None means latest / unspecified.",
    )


# Represents the file references associated with a workflow/operation, keyed by file type
class AssociatedFiles(BaseModel):
    """Grouped file references belonging to an operation or workflow."""

    arazzo: list[FileId] = Field(
        default_factory=list,
        description="List of Arazzo workflow/runner documents",
    )
    open_api: list[FileId] = Field(
        default_factory=list,
        description="List of OpenAPI specification files referenced by this entity",
    )


# Represents a single workflow entry in the 'workflows' dictionary
class WorkflowEntry(BaseModel):
    """A single workflow returned by :py:meth:`Jentic.load` (raw form).

    It keeps both the *friendly* ``workflow_id`` and the underlying ``workflow_uuid``
    so you can correlate search hits with runtime UUIDs.
    """

    workflow_id: str = Field(..., description="Human-readable ID inside the Arazzo doc")
    workflow_uuid: str = Field(..., description="Primary UUID assigned by the API Hub")
    name: str = Field(..., description="Workflow display name / summary")
    api_references: list[APIReference] = Field(
        default_factory=list,
        description="List of APIs invoked by this workflow",
    )
    files: AssociatedFiles = Field(
        ..., description="File IDs for all specs referenced by the workflow"
    )
    api_name: str = Field(
        default="",
        description="Back-compat field; primary API name if there is a single default",
    )
    api_names: list[str] | None = Field(
        default=None,
        description="All API names referenced by this workflow (if >1)",
    )


# Represents a single operation entry in the 'operations' dictionary
class OperationEntry(BaseModel):
    """Entry describing a single REST operation exposed by an API version."""

    id: str = Field(..., description="UUID of the operation (op_…)")
    api_name: str = Field(
        default="",
        description="Primary API name – kept for legacy reasons; prefer spec_info",
    )
    api_version_id: str = Field(..., description="UUID of the parent API version")
    operation_id: str | None = Field(
        default=None,
        description="OperationId inside the OpenAPI spec (if provided)",
    )
    path: str = Field(..., description="HTTP path template of the operation")
    method: str = Field(..., description="HTTP method in upper-case (GET, POST, …)")
    summary: str | None = Field(default=None, description="Short human-readable summary")
    files: AssociatedFiles = Field(..., description="Spec files associated with this operation")
    api_references: list[APIReference] | None = Field(
        default=None,
        description="Resolved API references (populated by load)",
    )
    spec_info: SpecInfo | None = Field(
        default=None,
        description="Vendor / name / version triple identifying the spec this operation belongs to",
    )


# The main response model
class GetFilesResponse(BaseModel):
    """Raw response from the *get-execution-files* endpoint."""

    files: dict[str, dict[str, FileEntry]] = Field(
        default_factory=dict,
        description="Mapping *file_type* → *file_id* → FileEntry for every spec file",
    )
    workflows: dict[str, WorkflowEntry] = Field(
        default_factory=dict,
        description="All workflows returned, keyed by workflow UUID",
    )
    operations: dict[str, OperationEntry] | None = Field(
        default=None,
        description="Operations returned (if requested), keyed by operation UUID",
    )


# Represents the details needed to execute a specific workflow
class WorkflowExecutionDetails(BaseModel):
    """Intermediate helper model used when generating runtime config."""

    arazzo_doc: dict[str, Any] | None = Field(
        default=None,
        description="Parsed Arazzo document for the workflow (None if missing)",
    )
    source_descriptions: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="OpenAPI specs keyed by filename for auth analysis",
    )
    friendly_workflow_id: str | None = Field(
        default=None,
        description="Human-readable ID inside the Arazzo document",
    )


class SearchResult(BaseModel):
    """Single hit returned by the semantic search endpoint."""

    id: str = Field(..., description="UUID of the matched entity (op_… / wf_…)")
    path: str = Field(..., description="HTTP path template of the operation (empty for workflows)")
    method: str = Field(..., description="HTTP method in upper-case (GET, POST, …)")
    api_name: str = Field(..., description="API name that owns the match")
    entity_type: str = Field(..., description="'operation' or 'workflow'")
    summary: str = Field(..., description="Short label or summary for the hit")
    description: str = Field(..., description="Longer textual description from the spec")
    match_score: float = Field(0.0, description="Semantic distance score (lower = better)")

    operation_id: str | None = Field(
        default=None,
        description="OpenAPI operationId (present for operation hits)",
    )
    workflow_id: str | None = Field(
        default=None,
        description="Friendly workflow_id (present for workflow hits)",
    )

    @model_validator(mode="before")
    @classmethod
    def set_data(cls, data: Any) -> dict[str, Any]:
        if data.get("entity_type") == "operation":
            summary = data.get("summary", "")
        else:
            summary = data.get("name", data.get("workflow_id", ""))

        if isinstance(data, dict):
            return {
                "id": data.get("id", ""),
                "entity_type": data.get("entity_type", ""),
                "summary": summary,
                "description": data.get("description", ""),
                "path": data.get("path", ""),
                "method": data.get("method", ""),
                "api_name": data.get("api_name", ""),
                "match_score": data.get("distance", 0.0),
                "operation_id": data.get("operation_id", None),
                "workflow_id": data.get("workflow_id", None),
            }
        return data


# Search request and response models #
class SearchRequest(BaseModel):
    """Parameters accepted by :py:meth:`Jentic.search`."""

    query: str = Field(..., description="Free-text query string (natural language)")
    limit: int = Field(default=5, description="Maximum number of results to return")
    apis: list[str] | None = Field(
        default=None,
        description="Optional list of API names to restrict the search to",
    )
    keywords: list[str] | None = Field(
        default=None,
        description="Optional list of keywords used to boost semantic search",
    )
    filter_by_credentials: bool = Field(
        default=True,
        description="When True, hide results the agent lacks credentials for",
    )


class SearchResponse(BaseModel):
    """Return value of :py:meth:`Jentic.search`."""

    results: list[SearchResult] = Field(
        default_factory=list,
        description="Rank-ordered list of operations and workflows that match the query",
    )
    total_count: int = Field(0, description="Total number of hits")
    query: str = Field(..., description="Echo of the original search string")


# Load Request
class LoadRequest(BaseModel):
    """Request model for :py:meth:`Jentic.load`."""

    ids: list[str] | None = Field(
        default=None,
        description="List of operation/workflow UUIDs to load",
    )

    def to_dict(self) -> dict[str, Any]:
        if self.ids is None:
            return {}

        workflow_uuids = []
        operation_uuids = []

        for id in self.ids:
            if id.startswith("wf_"):
                workflow_uuids.append(id)
            elif id.startswith("op_"):
                operation_uuids.append(id)

        return {
            "workflow_uuids": workflow_uuids,
            "operation_uuids": operation_uuids,
        }


class WorkflowDetail(BaseModel):
    """Detailed metadata for a workflow included in a runtime config."""

    description: str = Field(
        "",
        description="Markdown-compatible long description of the workflow",
    )
    id: str = Field(..., description="UUID of the workflow (wf_…)")
    summary: str = Field("", description="Short single-line summary")
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON-schema for workflow inputs (merged across steps)",
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON-schema describing the workflow outputs",
    )
    api_names: list[str] = Field(
        default_factory=list,
        description="List of API names invoked somewhere inside the workflow",
    )
    security_requirements: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Flattened security requirements keyed by source filename",
    )


class OperationDetail(BaseModel):
    """Rich description for an individual REST operation included in a runtime config.

    This structure is consumed by UI generators and by the AgentToolManager to
    create invocation-ready tool definitions.
    """

    id: str = Field(..., description="UUID of the operation (op_…)")
    method: str | None = Field(
        default=None,
        description="HTTP method (GET, POST, …). None for workflow-only entries.",
    )
    path: str | None = Field(
        default=None,
        description="HTTP path template. None when not applicable.",
    )
    summary: str | None = Field(
        default=None, description="Short summary extracted from the OpenAPI spec"
    )
    api_name: str | None = Field(
        default=None, description="API this operation belongs to (vendor/name)"
    )
    inputs: dict[str, Any] | None = Field(
        default=None,
        description="JSON-schema fragment describing the operation inputs",
    )
    outputs: dict[str, Any] | None = Field(
        default=None,
        description="JSON-schema fragment describing the operation outputs",
    )
    security_requirements: list[dict[str, Any]] | None = Field(
        default=None,
        description="Flattened list of security requirements for the operation",
    )


class LoadResponse(BaseModel):
    """Return value of :py:meth:`Jentic.load`."""

    tool_info: dict[str, OperationDetail | WorkflowDetail | None] = Field(
        default_factory=dict,
        description="Mapping of every requested UUID to its detailed schema",
    )

    @classmethod
    def from_get_files_response(cls, get_files_response: GetFilesResponse) -> "LoadResponse":
        # Transform LoadResponse to dict[str, Any]
        # This matches the agent_runtime.config parsing
        from jentic.lib.agent_runtime.config import JenticConfig

        # Get workflow and operation UUIDs
        workflow_uuids = (
            list(get_files_response.workflows.keys()) if get_files_response.workflows else []
        )
        operation_uuids = (
            list(get_files_response.operations.keys()) if get_files_response.operations else []
        )

        # Extract workflow details
        all_arazzo_specs, extracted_workflow_details = JenticConfig._extract_all_workflow_details(
            get_files_response, workflow_uuids
        )

        # Step 3: Extract operation details if present
        extracted_operation_details = {}
        if operation_uuids:
            extracted_operation_details = JenticConfig._extract_all_operation_details(
                get_files_response, operation_uuids
            )

        return LoadResponse(
            tool_info=cast(
                dict[str, OperationDetail | WorkflowDetail | None],
                {**extracted_operation_details, **extracted_workflow_details},
            ),
        )


class ExecutionRequest(BaseModel):
    """Payload expected by :py:meth:`Jentic.execute`."""

    id: str = Field(
        ...,
        description="UUID of the operation/workflow to execute (op_… or wf_…)",
    )
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input object matching the JSON schema returned by :py:meth:`Jentic.load`",
    )

    def to_dict(self) -> dict[str, Any]:
        # Transform the id to execution_type and uuid
        if self.id.startswith("op_"):
            execution_type = "operation"
        else:
            execution_type = "workflow"

        return {
            "execution_type": execution_type,
            "uuid": self.id,
            "inputs": self.inputs,
        }


class ExecuteResponse(BaseModel):
    """Return value of :py:meth:`Jentic.execute`."""

    success: bool = Field(..., description="True when the remote execution succeeded")
    status_code: int = Field(..., description="HTTP status code for the execution")
    output: Any | None = Field(
        default=None,
        description="Raw output produced by the operation/workflow (if any)",
    )
    error: str | None = Field(default=None, description="Error message when *success* is False")
    step_results: dict[str, Any] | None = Field(
        default=None,
        description="Per-step execution traces when the backend provides them",
    )
    inputs: dict[str, Any] | None = Field(
        default=None,
        description="Echo of the original inputs (useful for debugging)",
    )
