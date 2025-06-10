"""Tool execution library for Agent Runtime."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from oak_runner import OAKRunner, WorkflowExecutionResult, WorkflowExecutionStatus

from jentic import api
from jentic.api import JenticAPIClient
from jentic.api.api_hub import JenticAPIClient
from jentic.models import WorkflowExecutionDetails


# Define a WorkflowResult class to standardize results
@dataclass
class WorkflowResult:
    """Result of a workflow execution."""

    success: bool
    output: dict[str, Any] | None = None
    error: str | None = None
    step_results: dict[str, Any] | None = None
    inputs: dict[str, Any] | None = None


@dataclass
class OperationResult:
    """Result of an operation execution."""

    success: bool
    status_code: Optional[int] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None


# Setup logging
logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executor for AI tool calls to Arazzo workflows."""

    def __init__(self, api_hub_client: Optional[JenticAPIClient] = None):
        """Initialize the tool executor.

        Args:
            config: Configuration dictionary for the project.
        """

        # Initialize API Hub client
        self.api_hub_client = api_hub_client or JenticAPIClient()

    async def execute_workflow(self, workflow_uuid: str, inputs: Dict[str, Any]) -> WorkflowResult:
        """Executes a specified workflow using OAK runner.

        Args:
            workflow_uuid: The UUID of the workflow to execute.
            inputs: The input parameters for the workflow execution.

        Returns:
            The result of the workflow execution.
        """
        logger.info(f"Fetching execution files for workflow UUID: {workflow_uuid}")
        try:
            # Call the modified method with a single workflow ID
            exec_details: WorkflowExecutionDetails = (
                await self.api_hub_client.get_execution_details_for_workflow(workflow_uuid)
            )

            if exec_details is None:
                logger.error(
                    f"Execution details could not be retrieved for workflow_uuid: {workflow_uuid}."
                )
                return WorkflowResult(
                    success=False,
                    output=None,
                    error=f"Execution details not found for workflow {workflow_uuid}",
                )

            arazzo_doc = exec_details.arazzo_doc
            source_descriptions = exec_details.source_descriptions
            friendly_workflow_id = exec_details.friendly_workflow_id  # Use the internal ID

            if not arazzo_doc or not friendly_workflow_id:
                logger.error(
                    f"Missing Arazzo document or internal workflow ID for workflow_uuid: {workflow_uuid}."
                )
                return WorkflowResult(
                    success=False,
                    output=None,
                    error=f"Arazzo document or internal workflow ID missing for {workflow_uuid}",
                )

            # 4. Instantiate OAKRunner
            logger.debug(
                f"Instantiating OAKRunner for internal workflow ID: {friendly_workflow_id}"
            )
            runner = OAKRunner(
                arazzo_doc=arazzo_doc,
                source_descriptions=source_descriptions,
            )

            # 5. Execute the workflow using the INTERNAL workflow ID
            logger.debug(
                f"Running workflow {friendly_workflow_id} via OAKRunner with UUID {workflow_uuid}."
            )
            # Removed await as runner.execute_workflow seems synchronous based on TypeError
            execution_output: WorkflowExecutionResult = runner.execute_workflow(
                workflow_id=friendly_workflow_id, inputs=inputs
            )

            # 6. Process result and return WorkflowResult
            if execution_output.status == WorkflowExecutionStatus.WORKFLOW_COMPLETE:
                return WorkflowResult(
                    success=True,
                    output=execution_output.outputs
                )
            else:
                return WorkflowResult(
                    success=False,
                    error=execution_output.error or "Workflow execution failed.",
                    step_results=execution_output.step_outputs,
                    inputs=execution_output.inputs
                )

        except Exception as e:
            logger.exception(f"Error executing workflow {workflow_uuid}: {e}")
            return WorkflowResult(success=False, error=f"An unexpected error occurred: {e}")

    async def execute_operation(
        self,
        operation_uuid: str,
        inputs: Dict[str, Any],
    ) -> OperationResult:
        """
        Executes a specified API operation using OAKRunner after fetching required files from the API.

        Args:
            operation_uuid: The UUID of the operation to execute.
            inputs: Input parameters for the operation.
        Returns:
            An OperationResult object. If successful, `result.output` contains the
            operation's response body (or the full response if 'body' is not present).
            If unsuccessful, `result.error` contains an error message and `result.output`
            may contain the full response for context.
        """
        logger.info(f"Fetching execution files for operation UUID: {operation_uuid}")
        try:
            # Fetch operation execution files from the API
            exec_files_response = await self.api_hub_client.get_execution_files(
                operation_uuids=[operation_uuid]
            )
            if (
                not exec_files_response.operations
                or operation_uuid not in exec_files_response.operations
            ):
                logger.error(
                    f"Operation ID {operation_uuid} not found in execution files response."
                )
                return OperationResult(
                    success=False,
                    error=f"Operation ID {operation_uuid} not found in execution files response.",
                    inputs=inputs,
                )
            operation_entry = exec_files_response.operations[operation_uuid]

            # Prepare OpenAPI spec for OAKRunner
            openapi_content = None
            openapi_files = exec_files_response.files.get("open_api", {})
            if operation_entry.files.open_api:
                openapi_file_id = operation_entry.files.open_api[0].id
                if openapi_file_id in openapi_files:
                    openapi_content = openapi_files[openapi_file_id].content
            if not openapi_content:
                logger.error(f"OpenAPI spec not found for operation {operation_uuid}")
                return OperationResult(
                    success=False,
                    error=f"OpenAPI spec not found for operation {operation_uuid}",
                    inputs=inputs,
                )
            source_descriptions = {"default": openapi_content}

            # Prepare OAKRunner and execute the operation
            runner = OAKRunner(source_descriptions=source_descriptions)
            # Pass operation_uuid, path, and method from the operation_entry
            oak_result: Any = runner.execute_operation(
                inputs=inputs, operation_path=f"{operation_entry.method} {operation_entry.path}"
            )
            logger.debug(f"Operation execution result: {oak_result}")

            return self._process_operation_result(oak_result, operation_uuid, inputs)
        except Exception as e:
            logger.exception(f"Error executing operation {operation_uuid}: {e}")
            return OperationResult(
                success=False,
                error=str(e),
                inputs=inputs,
            )

    def _process_operation_result(
        self, oak_result: Dict[str, Any], operation_uuid: str, inputs: Dict[str, Any]
    ) -> "OperationResult":
        """Process the OAKRunner operation result, check status codes, and handle casting.

        Args:
            oak_result: The result dictionary from OAKRunner.execute_operation.
            operation_uuid: The UUID of the operation being executed, for logging.

        Returns:
            An OperationResult object.
        """
        status_code_uncast = oak_result.get("status_code")

        if status_code_uncast is None:
            logger.debug(
                f"Operation {operation_uuid} result dictionary does not contain 'status_code'. "
                f"Proceeding as if successful, returning body if present or full result."
            )
            return OperationResult(
                success=True,
                output=oak_result.get("body") if "body" in oak_result else oak_result,
                inputs=inputs,
            )

        if not isinstance(status_code_uncast, int):
            try:
                status_code = int(status_code_uncast)
                logger.debug(
                    f"Operation {operation_uuid} 'status_code' was {type(status_code_uncast).__name__} '{status_code_uncast}', "
                    f"successfully cast to int: {status_code}."
                )
            except (ValueError, TypeError):
                logger.debug(
                    f"Operation {operation_uuid} 'status_code' ('{status_code_uncast}') is not a valid integer and could not be cast. "
                    f"Marking as failure."
                )
                return OperationResult(
                    success=False,
                    error=f"Invalid status_code format: '{status_code_uncast}'. Expected an integer or integer-convertible value.",
                    output=oak_result,  # Include full OAK result for context on casting errors
                    inputs=inputs,
                )
        else:
            status_code = status_code_uncast  # It's already an int

        # status_code is now confirmed or cast to an integer
        if 200 <= status_code < 300:
            # Successful 2xx status code
            return OperationResult(
                success=True,
                status_code=status_code,
                output=oak_result.get("body") if "body" in oak_result else oak_result,
                inputs=inputs,
            )
        else:
            # Non-2xx status code, indicates an error
            body_content = oak_result.get("body")
            error_detail = ""

            if isinstance(body_content, dict):
                detail = body_content.get(
                    "error", body_content.get("message", body_content.get("detail"))
                )
                if detail is not None:
                    error_detail = str(detail)
                else:
                    error_detail = str(body_content)
            elif isinstance(body_content, (str, bytes)):
                try:
                    error_detail = (
                        body_content.decode()
                        if isinstance(body_content, bytes)
                        else body_content
                    )
                except UnicodeDecodeError:
                    error_detail = "Non-decodable binary content in body"
            elif body_content is not None:
                error_detail = str(body_content)

            return OperationResult(
                success=False,
                status_code=status_code,
                error=error_detail,
                output=oak_result,  # Return the full OAK result as output for context on errors
                inputs=inputs,
            )


    def _format_workflow_result(self, result: WorkflowResult) -> dict[str, Any]:
        """Format a workflow result for tool output.

        Args:
            result: Workflow execution result.

        Returns:
            Formatted result.
        """
        if not result.success:
            return {
                "success": False,
                "error": result.error or "Unknown error",
            }

        # Format a successful result
        output = {
            "success": True,
            "result": result.output,
        }

        # Add step information if available
        if result.step_results:
            output["steps"] = {}
            for step_id, step_result in result.step_results.items():
                # Handle step_result being a dict (raw step result from runner)
                # instead of a WorkflowResult object
                if isinstance(step_result, dict):
                    step_success = step_result.get("success", False)
                    step_output = step_result.get("outputs", {})
                    step_error = step_result.get("error", "")

                    output["steps"][step_id] = {"success": step_success, "output": step_output}

                    if not step_success and step_error:
                        output["steps"][step_id]["error"] = step_error
                else:
                    # Original code for WorkflowResult objects
                    output["steps"][step_id] = {
                        "success": step_result.success,
                        "output": step_result.output,
                    }
                    if not step_result.success:
                        output["steps"][step_id]["error"] = step_result.error

        return output
