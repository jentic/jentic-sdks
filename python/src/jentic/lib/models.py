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


class SearchResult(BaseModel):
    id: str
    path: str
    method: str
    api_name: str
    entity_type: str
    summary: str
    description: str
    match_score: float = 0.0

    operation_id: str | None = None
    workflow_id: str | None = None

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
    """Request model for  search."""

    query: str
    limit: int = 5
    apis: list[str] | None = None
    keywords: list[str] | None = None
    filter_by_credentials: bool = True


class SearchResponse(BaseModel):
    # Search All /combined results response
    results: list[SearchResult] = Field(
        default_factory=list, description="Operation and Workflow results"
    )
    total_count: int = Field(0, description="Total number of results")
    query: str = Field(..., description="Original search query")


# Load Request
class LoadRequest(BaseModel):
    ids: list[str] | None = None

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
    """Schema for a single workflow entry in the generated config."""

    description: str = ""
    id: str
    summary: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    api_names: list[str] = Field(default_factory=list)
    security_requirements: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Flattened security requirements keyed by source filename.",
    )


class OperationDetail(BaseModel):
    """Schema for a single operation entry in the generated config."""

    id: str
    method: str | None = None
    path: str | None = None
    summary: str | None = None
    api_name: str | None = None
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
    security_requirements: list[dict[str, Any]] | None = None


class LoadResponse(BaseModel):
    """Top-level model returned by `load`."""

    tool_info: dict[str, OperationDetail | WorkflowDetail | None] = Field(
        default_factory=dict,
        description="Results of the load operation, keyed by UUID",
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
    """
    Request model for execute.
    """

    id: str = Field(..., description="The UUID of the operation / workflow to execute.")
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary key-value inputs forwarded to the runner."
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
    success: bool
    output: dict[str, Any] | None = None
    error: str | None = None
    step_results: dict[str, Any] | None = None
    inputs: dict[str, Any] | None = None
