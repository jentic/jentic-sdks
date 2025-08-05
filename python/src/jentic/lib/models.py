from enum import Enum
from typing import Any, Dict, cast

from pydantic import BaseModel, Field, model_validator


# Represents a reference to a file ID
class FileId(BaseModel):
    id: str


# Represents the detailed file entry
class FileEntry(BaseModel):
    id: str
    filename: str
    type: str
    content: dict[str, Any]  # Content can be any valid JSON object
    source_path: str | None = None  # Contextual path for the file, e.g., from Arazzo spec_files

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
    api_id: str
    api_name: str
    api_version: str


class APIIdentifier(BaseModel):
    api_vendor: str
    api_name: str | None = None
    api_version: str | None = None


# Represents the spec info of an operation or workflow
class SpecInfo(BaseModel):
    api_vendor: str
    api_name: str
    api_version: str | None = None


# Represents the file references associated with a workflow/operation, keyed by file type
class AssociatedFiles(BaseModel):
    arazzo: list[FileId] = []
    open_api: list[FileId] = []


# Represents a single workflow entry in the 'workflows' dictionary
class WorkflowEntry(BaseModel):
    workflow_id: str
    workflow_uuid: str
    name: str
    api_references: list[APIReference]
    files: AssociatedFiles
    api_name: str = ""  # Default to empty string instead of None for better type safety
    api_names: list[str] | None = None


# Represents a single operation entry in the 'operations' dictionary
class OperationEntry(BaseModel):
    id: str
    api_name: str = ""  # Default to empty string instead of None for better type safety
    api_version_id: str
    operation_id: str | None = None
    path: str
    method: str
    summary: str | None = None
    files: AssociatedFiles
    api_references: list[APIReference] | None = None
    spec_info: SpecInfo | None = None


# The main response model
class GetFilesResponse(BaseModel):
    files: dict[str, dict[str, FileEntry]]  # FileType -> FileId -> FileEntry
    workflows: dict[str, WorkflowEntry]  # WorkflowUUID -> WorkflowEntry
    operations: dict[str, OperationEntry] | None = None  # OperationUUID -> OperationEntry


# Represents the details needed to execute a specific workflow
class WorkflowExecutionDetails(BaseModel):
    arazzo_doc: dict[str, Any] | None = None
    source_descriptions: dict[str, dict[str, Any]] = {}
    friendly_workflow_id: str | None = None


class BaseSearchResult(BaseModel):
    summary: str
    description: str
    match_score: float = 0.0


class WorkflowSearchResult(BaseSearchResult):
    workflow_id: str
    api_name: str

    @model_validator(mode="before")
    @classmethod
    def set_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "workflow_id": data.get("id", ""),
            "summary": data.get("name", data.get("workflow_id", "")),  # TODO - no summary?
            "description": data.get("description", ""),
            "api_name": data.get("api_name", ""),
            "match_score": data.get(
                "distance", 0.0
            ),  # TODO - change to distance, or rank or something?
        }


class OperationSearchResult(BaseSearchResult):
    operation_uuid: str
    path: str
    method: str
    api_name: str

    @model_validator(mode="before")
    @classmethod
    def set_data(cls, data: Any) -> dict[str, Any]:
        if isinstance(data, dict):
            return {
                "operation_uuid": data.get("id", ""),
                "summary": data.get("summary", ""),
                "description": data.get("description", ""),
                "path": data.get("path", ""),
                "method": data.get("method", ""),
                "api_name": data.get("api_name", ""),
                "match_score": data.get("distance", 0.0),
            }
        return data


# Search request and response models #
class SearchRequest(BaseModel):
    """Request model for  search."""

    query: str
    limit: int = 5
    apis: list[str] | None = None
    keywords: list[str] | None = None
    filter_by_credentials: bool = True


class SearchResponse(BaseModel):
    # Search All /combined results response
    results: list[WorkflowSearchResult | OperationSearchResult] = Field(
        default_factory=list, description="Operation and Workflow results"
    )
    total_count: int = Field(0, description="Total number of results")
    query: str = Field(..., description="Original search query")


# Load Request
class LoadRequest(BaseModel):
    workflow_uuids: list[str] | None = None
    operation_uuids: list[str] | None = None


class WorkflowDetail(BaseModel):
    """Schema for a single workflow entry in the generated config."""

    description: str = ""
    workflow_uuid: str
    summary: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    api_names: list[str] = Field(default_factory=list)
    security_requirements: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Flattened security requirements keyed by source filename.",
    )


class OperationDetail(BaseModel):
    """Schema for a single operation entry in the generated config."""

    operation_uuid: str
    method: str | None = None
    path: str | None = None
    summary: str | None = None
    api_name: str | None = None
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
    security_requirements: list[dict[str, Any]] | None = None


class LoadResponse(BaseModel):
    """Top-level model returned by `load`."""

    version: str = "1.0"
    workflows: Dict[str, WorkflowDetail] = Field(
        default_factory=dict,
        description="Friendly workflow ID → details",
    )
    operations: Dict[str, OperationDetail] = Field(
        default_factory=dict,
        description="Operation UUID → details",
    )

    @classmethod
    def from_get_files_response(cls, get_files_response: GetFilesResponse) -> "LoadResponse":
        # Transform LoadResponse to dict[str, Any]
        # This matches the agent_runtime.config parsing
        from jentic.lib.agent_runtime.config import JenticConfig

        # Get workflow and operation UUIDs
        workflow_uuids = list(get_files_response.workflows.keys())
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
            version="1.0",
            workflows=cast(dict[str, WorkflowDetail], extracted_workflow_details),
            operations=cast(dict[str, OperationDetail], extracted_operation_details),
        )


class ExecutionType(str, Enum):
    """Allowed execution types handled by the Lambda."""

    OPERATION = "operation"
    WORKFLOW = "workflow"


class ExecutionRequest(BaseModel):
    """
    Request model for execute.
    """

    execution_type: str = Field(
        ...,
        description="Whether the request should run a single *operation* or an entire *workflow*.",
    )
    uuid: str = Field(..., description="The UUID of the operation / workflow to execute.")
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary key-value inputs forwarded to the runner."
    )


class ExecuteResponse(BaseModel):
    success: bool
    output: dict[str, Any] | None = None
    error: str | None = None
    step_results: dict[str, Any] | None = None
    inputs: dict[str, Any] | None = None
