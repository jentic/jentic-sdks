from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Represents a reference to a file ID
class FileId(BaseModel):
    id: str


# Represents the detailed file entry
class FileEntry(BaseModel):
    id: str
    filename: str
    type: str
    content: Dict[str, Any]  # Content can be any valid JSON object
    oak_path: Optional[str] = None  # Contextual path for the file, e.g., from Arazzo spec_files


# Represents an API reference within a workflow
class APIReference(BaseModel):
    api_id: str
    api_name: str
    api_version: str


# Represents the spec info of an operation or workflow
class SpecInfo(BaseModel):
    api_vendor: str
    api_name: str
    api_version: str | None = None


# Represents the file references associated with a workflow/operation, keyed by file type
class AssociatedFiles(BaseModel):
    arazzo: List[FileId] = []
    open_api: List[FileId] = []


# Represents a single workflow entry in the 'workflows' dictionary
class WorkflowEntry(BaseModel):
    workflow_id: str
    workflow_uuid: str
    name: str
    api_references: List[APIReference]
    files: AssociatedFiles
    api_name: str = ""  # Default to empty string instead of None for better type safety
    api_names: Optional[List[str]] = None


# Represents a single operation entry in the 'operations' dictionary
class OperationEntry(BaseModel):
    id: str
    api_name: str = ""  # Default to empty string instead of None for better type safety
    api_version_id: str
    operation_id: Optional[str] = None
    path: str
    method: str
    summary: Optional[str] = None
    files: AssociatedFiles
    api_references: Optional[List[APIReference]] = None
    spec_info: Optional[SpecInfo] = None


# The main response model
class GetFilesResponse(BaseModel):
    files: Dict[str, Dict[str, FileEntry]]  # FileType -> FileId -> FileEntry
    workflows: Dict[str, WorkflowEntry]  # WorkflowUUID -> WorkflowEntry
    operations: Optional[Dict[str, OperationEntry]] = None  # OperationUUID -> OperationEntry


# Represents the details needed to execute a specific workflow
class WorkflowExecutionDetails(BaseModel):
    arazzo_doc: Optional[Dict[str, Any]] = None
    source_descriptions: Dict[str, Dict[str, Any]] = {}
    friendly_workflow_id: Optional[str] = None


class ApiCapabilitySearchRequest(BaseModel):
    """Request model for API capability search."""

    capability_description: str
    keywords: list[str] | None = None
    max_results: int = 5
    api_names: list[str] | None = None


class BaseSearchResult(BaseModel):
    summary: str
    description: str
    match_score: float = 0.0


class WorkflowSearchResult(BaseSearchResult):
    workflow_id: str
    api_name: str


class OperationSearchResult(BaseSearchResult):
    operation_uuid: str
    path: str
    method: str
    api_name: str


class APISearchResults(BaseModel):
    workflows: list[WorkflowSearchResult]
    operations: list[OperationSearchResult]
