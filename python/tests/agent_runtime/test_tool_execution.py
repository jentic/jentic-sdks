"""Unit tests for the TaskExecutor class in tool_execution.py."""

"""MOSTLY AI GENERATED"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from jentic.agent_runtime.tool_execution import (
    TaskExecutor,
)
from jentic.api import JenticAPIClient
from jentic.models import (
    AssociatedFiles,
    FileId,
    GetFilesResponse,
    FileEntry,
    OperationEntry,
    WorkflowEntry,
    WorkflowExecutionDetails,
)
from oak_runner import WorkflowExecutionResult as OakWorkflowExecutionResult, WorkflowExecutionStatus


@pytest.fixture
def minimal_config():
    """Provide a minimal configuration for testing."""
    return {"runtime": {"log_level": "DEBUG"}, "test_api": {"base_url": "https://api.example.com"}}


@pytest.fixture
def comprehensive_config():
    """Provide a more comprehensive configuration for testing."""
    return {
        "runtime": {"log_level": "INFO", "tool_format": "chatgpt"},
        "test_api": {
            "base_url": "https://api.example.com",
            "auth": {"type": "basic", "username": "test_user", "password": "test_password"},
        },
        "weather_api": {
            "base_url": "https://weather.example.com",
            "auth": {"type": "bearer", "token": "test_token"},
        },
        "email_api": {
            "base_url": "https://email.example.com",
            "auth": {
                "type": "oauth2",
                "client_id": "client_123",
                "client_secret": "secret_456",
                "scopes": ["read", "write"],
            },
        },
    }


@pytest_asyncio.fixture
async def mock_api_hub_client():
    """Create a mocked JenticAPIClient."""
    with patch(
        "jentic.agent_runtime.tool_execution.JenticAPIClient", autospec=True
    ) as mock_client_class:
        mock_client = AsyncMock(spec=JenticAPIClient)
        mock_client_class.return_value = mock_client
        yield mock_client


class TestWorkflowExecution:
    """Test suite for workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, mock_api_hub_client):
        """Test successful workflow execution."""
        # Prepare test data
        workflow_id = "test_workflow_uuid"  # External UUID
        friendly_workflow_id = "internal_test_workflow"  # Internal ID from API
        parameters = {"param1": "value1"}
        mock_arazzo_doc = {"info": "mock arazzo"}
        mock_source_descriptions = {"mock_source": {"openapi": "3.0"}}

        # Setup mock API Hub response for the renamed method
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Create a mock runner
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()  # OAKRunner.execute_workflow is synchronous
            # Update return value structure for OAKRunner
            mock_runner.execute_workflow.return_value = OakWorkflowExecutionResult(
                status=WorkflowExecutionStatus.WORKFLOW_COMPLETE,
                workflow_id=friendly_workflow_id,
                outputs={"final_output": "success"}
            )
            mock_runner_class.return_value = mock_runner

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  # Pass required api_hub_client

            # Call the method
            result = await executor.execute_workflow(workflow_id, parameters)

            # Verify the calls
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner_class.assert_called_once_with(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
            )
            # Verify execute_workflow is called with the INTERNAL ID
            mock_runner.execute_workflow.assert_called_once_with(
                workflow_id=friendly_workflow_id, inputs=parameters
            )

            # Verify the result
            assert result.success is True
            assert result.output == {"final_output": "success"}
            assert result.error is None
            assert result.step_results is None # Not populated on success by TaskExecutor
            assert result.inputs is None # Not populated on success by TaskExecutor

    @pytest.mark.asyncio
    async def test_execute_workflow_runner_returns_error(self, mock_api_hub_client): 
        """Test workflow execution when the runner returns an error status."""
        workflow_id = "test_workflow_runner_error_uuid"
        friendly_workflow_id = "internal_test_workflow_runner_error"
        parameters = {"param1": "value1"}
        mock_arazzo_doc = {"info": "mock arazzo runner error"}
        mock_source_descriptions = {"mock_source_runner_error": {}}
        expected_step_outputs = {"step1": "failed due to X"}
        expected_error_message = "Runner processing failed"

        # Setup mock API Hub response
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Create a mock runner that returns an error status
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_workflow.return_value = OakWorkflowExecutionResult(
                status=WorkflowExecutionStatus.ERROR,
                workflow_id=friendly_workflow_id,
                error=expected_error_message,
                outputs=None, 
                step_outputs=expected_step_outputs,
                inputs=parameters
            )
            mock_runner_class.return_value = mock_runner

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Call the method
            result = await executor.execute_workflow(workflow_id, parameters)

            # Verify the calls
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner_class.assert_called_once_with(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
            )
            # Verify execute_workflow is called with the INTERNAL ID
            mock_runner.execute_workflow.assert_called_once_with(
                workflow_id=friendly_workflow_id, inputs=parameters
            )

            # Verify the result
            assert result.success is False
            assert result.error == expected_error_message
            assert result.output is None
            assert result.step_results == expected_step_outputs
            assert result.inputs == parameters

    @pytest.mark.asyncio
    async def test_execute_workflow_api_details_error(self, mock_api_hub_client):
        """Test workflow execution when fetching execution details fails."""
        workflow_id = "test_workflow_api_fail"
        parameters = {"param1": "value1"}

        # Setup mock API Hub to return an empty dictionary (details not found)
        mock_api_hub_client.get_execution_details_for_workflow.return_value = None

        # Patch OAKRunner to ensure it's not called
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Call the method
            result = await executor.execute_workflow(workflow_id, parameters)

            # Assertions
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner_class.assert_not_called()  
            assert result.success is False
            assert f"Execution details not found for workflow {workflow_id}" == result.error

    @pytest.mark.asyncio
    async def test_execute_workflow_exception(self, mock_api_hub_client):
        """Test workflow execution when an unexpected exception occurs (e.g., runner init)."""
        workflow_id = "test_workflow_unexpected_fail"
        friendly_workflow_id = "internal_unexpected_fail"
        parameters = {"param1": "value1"}
        mock_arazzo_doc = {"info": "mock arazzo unexpected"}
        mock_source_descriptions = {}

        # Setup mock API Hub response for the renamed method
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Mock runner class to raise an exception during instantiation
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner_class.side_effect = Exception("Runner Init Error")

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Call the method
            result = await executor.execute_workflow(workflow_id, parameters)

            # Verify the calls
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            # Runner execute is not called if init fails

            # Verify the result
            assert result.success is False
            assert "Runner Init Error" in result.error


class TestCompleteWorkflowExecution:
    """Test suite for complete workflow execution scenarios."""

    @pytest.mark.asyncio
    async def test_complete_execution_with_multiple_steps(self, mock_api_hub_client):
        """Test a complete workflow execution that conceptually involves multiple steps (mocked as one runner call)."""
        workflow_id = "multi_step_workflow_uuid"
        friendly_workflow_id = "internal_multi_step"
        parameters = {"initial_input": "start"}
        arazzo_doc = {"info": "multi-step arazzo"}
        source_descriptions = {"multi_step_source": {}}

        # Setup mock API Hub response
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=arazzo_doc,
                source_descriptions=source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Mock the runner
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()  
            # Update return value structure
            mock_runner.execute_workflow.return_value = OakWorkflowExecutionResult(
                status=WorkflowExecutionStatus.WORKFLOW_COMPLETE,
                workflow_id=friendly_workflow_id,
                outputs={"final_output": "success"}
            )
            mock_runner_class.return_value = mock_runner

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Execute the workflow
            result = await executor.execute_workflow(workflow_id, parameters)

            # Assertions
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner_class.assert_called_once_with(
                arazzo_doc=arazzo_doc,
                source_descriptions=source_descriptions,
            )
            mock_runner.execute_workflow.assert_called_once_with(
                workflow_id=friendly_workflow_id, inputs=parameters
            )
            assert result.success is True
            assert result.output == {"final_output": "success"}

    @pytest.mark.asyncio
    async def test_workflow_with_empty_parameters(self, mock_api_hub_client):
        """Test executing a workflow with an empty parameters dictionary."""
        workflow_id = "empty_params_workflow_uuid"
        friendly_workflow_id = "internal_empty_params"
        mock_arazzo_doc = {"some_key": "some_value"}  
        mock_source_descriptions = {}

        # Setup mock API Hub response
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Mock the runner
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()  
            # Update return value structure
            mock_runner.execute_workflow.return_value = OakWorkflowExecutionResult(
                status=WorkflowExecutionStatus.WORKFLOW_COMPLETE,
                workflow_id=friendly_workflow_id,
                outputs={"output": "empty_params_success"}
            )
            mock_runner_class.return_value = mock_runner

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Call the method with empty parameters
            result = await executor.execute_workflow(workflow_id, {})

            # Assertions
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner.execute_workflow.assert_called_once_with(
                workflow_id=friendly_workflow_id, inputs={}
            )
            assert result.success is True
            assert result.output == {"output": "empty_params_success"}

    @pytest.mark.asyncio
    async def test_workflow_execution_with_no_outputs(self, mock_api_hub_client):
        """Test workflow execution where the runner returns no specific outputs."""
        workflow_id = "no_output_workflow_uuid"
        friendly_workflow_id = "internal_no_output"
        parameters = {"input": "data"}
        mock_arazzo_doc = {"some_key": "some_value"}  
        mock_source_descriptions = {}

        # Setup mock API Hub response
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Mock the runner to return an empty dictionary for outputs
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()  
            # Update return value structure
            mock_runner.execute_workflow.return_value = OakWorkflowExecutionResult(
                status=WorkflowExecutionStatus.WORKFLOW_COMPLETE,
                workflow_id=friendly_workflow_id,
                outputs={}
            )
            mock_runner_class.return_value = mock_runner

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Call the method
            result = await executor.execute_workflow(workflow_id, parameters)

            # Assertions
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner.execute_workflow.assert_called_once_with(
                workflow_id=friendly_workflow_id, inputs=parameters
            )
            assert result.success is True
            assert result.output == {}  
            assert result.error is None


class TestEdgeCases:
    """Tests covering edge cases and specific scenarios for workflow execution."""

    @pytest.mark.asyncio
    async def test_workflow_with_empty_parameters(self, mock_api_hub_client):
        """Test executing a workflow with an empty parameters dictionary."""
        workflow_id = "edge_empty_params_workflow_uuid"
        friendly_workflow_id = "internal_edge_empty_params"
        mock_arazzo_doc = {"some_key": "some_value"}  
        mock_source_descriptions = {}

        # Setup mock API Hub response
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Mock the runner
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()  
            # Update return value structure
            mock_runner.execute_workflow.return_value = OakWorkflowExecutionResult(
                status=WorkflowExecutionStatus.WORKFLOW_COMPLETE,
                workflow_id=friendly_workflow_id,
                outputs={"output": "empty_params_success"}
            )
            mock_runner_class.return_value = mock_runner

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Call the method with empty parameters
            result = await executor.execute_workflow(workflow_id, {})

            # Assertions
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner.execute_workflow.assert_called_once_with(
                workflow_id=friendly_workflow_id, inputs={}
            )
            assert result.success is True
            assert result.output == {"output": "empty_params_success"}

    @pytest.mark.asyncio
    async def test_workflow_with_alternate_complete_status(self, mock_api_hub_client):
        """Test workflow execution with an alternate (but valid) completion status."""
        workflow_id = "alt_complete_workflow_uuid"
        friendly_workflow_id = "internal_alt_complete"
        mock_arazzo_doc = {"some_key": "some_value"}  
        mock_source_descriptions = {}

        # Setup mock API Hub response
        mock_api_hub_client.get_execution_details_for_workflow.return_value = (
            WorkflowExecutionDetails(
                arazzo_doc=mock_arazzo_doc,
                source_descriptions=mock_source_descriptions,
                friendly_workflow_id=friendly_workflow_id,
            )
        )

        # Create mock runner
        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()  
            # Runner returns final result directly
            # Update return value structure
            mock_runner.execute_workflow.return_value = OakWorkflowExecutionResult(
                status=WorkflowExecutionStatus.WORKFLOW_COMPLETE,
                workflow_id=friendly_workflow_id,
                outputs={"result": "success"}
            )
            mock_runner_class.return_value = mock_runner

            # Create the tool executor
            executor = TaskExecutor(mock_api_hub_client)  

            # Call the method
            result = await executor.execute_workflow(workflow_id, {})

            # Assertions
            mock_api_hub_client.get_execution_details_for_workflow.assert_called_once_with(
                workflow_id
            )
            mock_runner.execute_workflow.assert_called_once_with(
                workflow_id=friendly_workflow_id, inputs={}
            )
            assert result.success is True
            assert result.output == {"result": "success"}


class TestOperationExecution:
    """Test suite for operation execution."""

    @pytest.mark.asyncio
    async def test_execute_operation_success(self, mock_api_hub_client):
        """Test successful operation execution with a 200 status and body."""
        operation_uuid = "op_success_uuid"
        inputs = {"param": "value"}
        mock_openapi_content = {"openapi": "3.0.0", "info": {"title": "Test API"}}
        mock_operation_entry = OperationEntry(
            api_version_id="v1",
            id=operation_uuid,
            method="GET",
            path="/test",
            files=AssociatedFiles(open_api=[FileId(id="openapi_file_id")]),
        )
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"openapi_file_id": FileEntry(id="openapi_file_id", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        oak_response_body = {"data": "success_data"}
        oak_full_response = {"status_code": 200, "body": oak_response_body, "headers": {}}

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_full_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            mock_api_hub_client.get_execution_files.assert_called_once_with(operation_uuids=[operation_uuid])
            mock_runner_class.assert_called_once_with(source_descriptions={"default": mock_openapi_content})
            mock_runner.execute_operation.assert_called_once_with(
                inputs=inputs, operation_path=f"{mock_operation_entry.method} {mock_operation_entry.path}"
            )

            assert result.success is True
            assert result.status_code == 200
            assert result.output == oak_response_body
            assert result.error is None
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_success_no_body(self, mock_api_hub_client):
        """Test successful operation execution with 200 status but no 'body' key in OAK result."""
        operation_uuid = "op_success_no_body_uuid"
        inputs = {}
        mock_openapi_content = {"openapi": "3.0.0"}
        mock_operation_entry = OperationEntry(api_version_id="v1", id=operation_uuid, method="POST", path="/submit", files=AssociatedFiles(open_api=[FileId(id="f1")]))
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"f1": FileEntry(id="f1", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        oak_full_response = {"status_code": 204, "headers": {"X-Custom": "value"}} # No body for 204

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_full_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            assert result.success is True
            assert result.status_code == 204
            assert result.output == oak_full_response # Should return the full OAK result
            assert result.error is None
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_api_error_4xx(self, mock_api_hub_client):
        """Test operation execution with a 400 client error."""
        operation_uuid = "op_client_error_uuid"
        inputs = {"bad_param": "invalid"}
        mock_openapi_content = {"openapi": "3.0.0"}
        mock_operation_entry = OperationEntry(api_version_id="v1", id=operation_uuid, method="GET", path="/test", files=AssociatedFiles(open_api=[FileId(id="f1")]))
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"f1": FileEntry(id="f1", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        error_detail = {"error": "Bad Request", "message": "Invalid parameter provided"}
        oak_full_response = {"status_code": 400, "body": error_detail, "headers": {}}

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_full_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            assert result.success is False
            assert result.status_code == 400
            # The error message is now just the detail from the body
            assert result.error == error_detail["error"]
            assert result.output == oak_full_response # Full OAK response in output for context
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_api_error_5xx(self, mock_api_hub_client):
        """Test operation execution with a 500 server error."""
        operation_uuid = "op_server_error_uuid"
        inputs = {}
        mock_openapi_content = {"openapi": "3.0.0"}
        mock_operation_entry = OperationEntry(api_version_id="v1", id=operation_uuid, method="GET", path="/status", files=AssociatedFiles(open_api=[FileId(id="f1")]))
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"f1": FileEntry(id="f1", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        oak_full_response = {"status_code": 503, "body": "Service Unavailable", "headers": {}}

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_full_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            assert result.success is False
            assert result.status_code == 503
            assert result.error == "Service Unavailable"
            assert result.output == oak_full_response
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_status_code_as_string(self, mock_api_hub_client):
        """Test successful operation when status_code is a convertible string."""
        operation_uuid = "op_status_string_uuid"
        inputs = {}
        mock_openapi_content = {"openapi": "3.0.0"}
        mock_operation_entry = OperationEntry(api_version_id="v1", id=operation_uuid, method="GET", path="/test", files=AssociatedFiles(open_api=[FileId(id="f1")]))
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"f1": FileEntry(id="f1", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        oak_response_body = {"message": "OK"}
        oak_full_response = {"status_code": "201", "body": oak_response_body, "headers": {}}

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_full_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            assert result.success is True
            assert result.status_code == 201 # Should be cast to int
            assert result.output == oak_response_body
            assert result.error is None
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_status_code_invalid_string(self, mock_api_hub_client):
        """Test failure when status_code is a non-convertible string."""
        operation_uuid = "op_status_invalid_string_uuid"
        inputs = {}
        mock_openapi_content = {"openapi": "3.0.0"}
        mock_operation_entry = OperationEntry(api_version_id="v1", id=operation_uuid, method="GET", path="/test", files=AssociatedFiles(open_api=[FileId(id="f1")]))
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"f1": FileEntry(id="f1", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        oak_full_response = {"status_code": "OK_NOT_A_NUMBER", "body": "Error", "headers": {}}

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_full_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            assert result.success is False
            assert result.status_code is None # Status code is not set on casting failure
            assert "Invalid status_code format: 'OK_NOT_A_NUMBER'" in result.error
            assert result.output == oak_full_response # Full OAK response in output
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_missing_status_code(self, mock_api_hub_client):
        """Test behavior when OAKRunner result is missing 'status_code'."""
        operation_uuid = "op_missing_status_uuid"
        inputs = {}
        mock_openapi_content = {"openapi": "3.0.0"}
        mock_operation_entry = OperationEntry(api_version_id="v1", id=operation_uuid, method="GET", path="/test", files=AssociatedFiles(open_api=[FileId(id="f1")]))
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"f1": FileEntry(id="f1", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        oak_response_body = {"data": "some_data"}
        # OAK result missing status_code
        oak_full_response = {"body": oak_response_body, "headers": {}}

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_full_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            # Current logic defaults to success if status_code is missing
            assert result.success is True
            assert result.status_code is None
            assert result.output == oak_response_body
            assert result.error is None
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_runner_returns_not_dict(self, mock_api_hub_client):
        """Test behavior when OAKRunner returns a non-dictionary result."""
        operation_uuid = "op_runner_not_dict_uuid"
        inputs = {}
        mock_openapi_content = {"openapi": "3.0.0"}
        mock_operation_entry = OperationEntry(api_version_id="v1", id=operation_uuid, method="GET", path="/test", files=AssociatedFiles(open_api=[FileId(id="f1")]))
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"f1": FileEntry(id="f1", filename="spec.json", type="open_api", content=mock_openapi_content)}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        # OAKRunner returns a string instead of a dict
        oak_non_dict_response = "This is not a dictionary"

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.execute_operation.return_value = oak_non_dict_response
            mock_runner_class.return_value = mock_runner

            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            assert result.success is False
            assert "object has no attribute 'get'" in result.error
            assert result.status_code is None
            assert result.output is None
            assert result.inputs == inputs


    @pytest.mark.asyncio
    async def test_execute_operation_no_operation_entry(self, mock_api_hub_client):
        """Test failure when operation_uuid is not found in API Hub response."""
        operation_uuid = "op_not_found_uuid"
        inputs = {}
        # API Hub returns a response where the operation_uuid is not a key
        mock_exec_files_response = GetFilesResponse(workflows={}, operations={}, files={})
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            mock_runner_class.assert_not_called() # OAKRunner should not be initialized or called
            assert result.success is False
            assert result.error == f"Operation ID {operation_uuid} not found in execution files response."
            assert result.status_code is None
            assert result.output is None
            assert result.inputs == inputs

    @pytest.mark.asyncio
    async def test_execute_operation_no_openapi_spec(self, mock_api_hub_client):
        """Test failure when OpenAPI spec content is missing."""
        operation_uuid = "op_no_openapi_uuid"
        inputs = {}
        # OperationEntry exists, but its files list is empty or points to a non-existent/empty file
        mock_operation_entry = OperationEntry(
            api_version_id="v1",
            id=operation_uuid,
            method="GET",
            path="/test",
            files=AssociatedFiles(open_api=[FileId(id="openapi_file_id")]), # Points to a file
        )
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"openapi_file_id": FileEntry(id="openapi_file_id", filename="spec.json", type="open_api", content={})}}, # File content is empty
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            mock_runner_class.assert_not_called()
            assert result.success is False
            assert result.error == f"OpenAPI spec not found for operation {operation_uuid}"
            assert result.status_code is None
            assert result.output is None
            assert result.inputs == inputs
            
    @pytest.mark.asyncio
    async def test_execute_operation_no_openapi_file_entry_in_files(self, mock_api_hub_client):
        """Test failure when OpenAPI spec file ID from operation_entry.files.open_api is not in exec_files_response.files."""
        operation_uuid = "op_no_openapi_file_entry_uuid"
        inputs = {}
        mock_operation_entry = OperationEntry(
            api_version_id="v1",
            id=operation_uuid,
            method="GET",
            path="/test",
            files=AssociatedFiles(open_api=[FileId(id="actual_openapi_file_id")]), 
        )
        # The 'files' dict does not contain 'actual_openapi_file_id' under 'open_api'
        mock_exec_files_response = GetFilesResponse(workflows={}, 
            operations={operation_uuid: mock_operation_entry},
            files={"open_api": {"some_other_file_id": FileEntry(id="some_other_file_id", filename="spec.json", type="open_api", content={"openapi":"3.0"})}},
        )
        mock_api_hub_client.get_execution_files.return_value = mock_exec_files_response

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            mock_runner_class.assert_not_called()
            assert result.success is False
            assert result.error == f"OpenAPI spec not found for operation {operation_uuid}"
            assert result.status_code is None
            assert result.output is None
            assert result.inputs == inputs


    @pytest.mark.asyncio
    async def test_execute_operation_general_exception_api_call(self, mock_api_hub_client):
        """Test failure when get_execution_files raises an unexpected exception."""
        operation_uuid = "op_general_exception_uuid"
        inputs = {}
        expected_exception = RuntimeError("Network Error")
        mock_api_hub_client.get_execution_files.side_effect = expected_exception

        with patch("jentic.agent_runtime.tool_execution.OAKRunner") as mock_runner_class:
            executor = TaskExecutor(api_hub_client=mock_api_hub_client)
            result = await executor.execute_operation(operation_uuid, inputs)

            mock_runner_class.assert_not_called()
            assert result.success is False
            assert str(expected_exception) in result.error
            assert result.status_code is None
            assert result.output is None
            assert result.inputs == inputs


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
