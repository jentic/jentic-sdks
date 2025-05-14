"""Unit tests for the TaskExecutor class in tool_execution.py."""

"""MOSTLY AI GENERATED"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from jentic.agent_runtime.tool_execution import TaskExecutor, WorkflowResult
from jentic.api import JenticAPIClient
from jentic.models import WorkflowExecutionDetails
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


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
