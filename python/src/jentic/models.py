from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# Represents a reference to a file ID
class FileId(BaseModel):
    id: str


# Represents the detailed file entry
class FileEntry(BaseModel):
    id: str
    filename: str
    type: str
    content: Dict[str, Any]  # Content can be any valid JSON object
    source_path: Optional[str] = None  # Contextual path for the file, e.g., from Arazzo spec_files
    
    @model_validator(mode='before')
    @classmethod
    def handle_oak_path_alias(cls, values):
        """Handle backward compatibility for oak_path field name."""
        if isinstance(values, dict):
            # If oak_path is provided but source_path is not, use oak_path
            if 'oak_path' in values and 'source_path' not in values:
                values['source_path'] = values.pop('oak_path')
            # If both are provided, prefer source_path and remove oak_path
            elif 'oak_path' in values and 'source_path' in values:
                values.pop('oak_path')
        return values
    
    @property
    def oak_path(self) -> Optional[str]:
        """Backward compatibility property for oak_path."""
        return self.source_path


# Represents an API reference within a workflow
class APIReference(BaseModel):
    api_id: str
    api_name: str
    api_version: str


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
