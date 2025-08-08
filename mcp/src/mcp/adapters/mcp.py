"""MCP adapter for the Jentic MCP Plugin."""

import logging
from typing import Any
import os
import httpx

from jentic import Jentic, SearchRequest, LoadRequest, ExecutionRequest, ExecuteResponse

from mcp.core.generators.code_generator import generate_code_sample
from mcp import version

class MCPAdapter:
    """Model Configuration Protocol adapter for the Jentic MCP Plugin."""

    def __init__(self):
        """Initialize the MCP adapter."""
        self.jentic = Jentic()

    async def search_api_capabilities(self, request: dict[str, Any]) -> dict[str, Any]:
        """MCP endpoint for searching API capabilities.

        Args:
            request: MCP tool request parameters.

        Returns:
            MCP tool response.
        """
        # Build SearchRequest using the new SDK
        search_request = SearchRequest(
            query=request.get("capability_description") or request.get("query", ""),
            keywords=request.get("keywords"),
            limit=request.get("max_results", 5),
            apis=request.get("api_names"),
        )

        search_response = await self.jentic.search(search_request)

        # We adopt the unified results list returned by SearchResponse
        response_data = search_response.model_dump(exclude_none=False)
        return {
            "result": {
                "matches": response_data,
                "query": search_request.query,
                "total_matches": search_response.total_count,
            }
        }

    async def generate_runtime_config(self, request: dict[str, Any]) -> dict[str, Any]:
        """MCP endpoint for generating a configuration file from a selection set.

        Args:
            request: MCP tool request parameters.

        Returns:
            MCP tool response.
        """
        # Get the workflow and operation UUIDs from the request
        workflow_uuids = request.get("workflow_uuids", [])
        if isinstance(workflow_uuids, str):
            workflow_uuids = [workflow_uuids]
        operation_uuids = request.get("operation_uuids", [])
        if isinstance(operation_uuids, str):
            operation_uuids = [operation_uuids]
        
        # Get the API name or use empty string as default
        api_name = request.get("api_name", "")

        logger = logging.getLogger(__name__)
        logger.debug(
            f"Generating config with workflow_uuids: {workflow_uuids}, operation_uuids: {operation_uuids}, api_name: {api_name}"
        )

        try:
            # In generate_runtime_config method replace load_execution_info call
            load_request = LoadRequest(
                ids=workflow_uuids + operation_uuids,
            )
            load_response = await self.jentic.load(load_request)
            result = load_response.model_dump(exclude_none=False)
            return {"result": result}

        except ValueError as e:
            logger.error(f"Error generating config: {str(e)}")
            return {
                "result": {
                    "success": False,
                    "operation_uuids": operation_uuids,
                    "workflow_uuids": workflow_uuids,
                    "api_name": api_name,
                    "message": str(e),
                    "config": {},
                }
            }

    async def generate_code_sample(self, request: dict[str, Any]) -> dict[str, Any]:
        """MCP endpoint for generating code samples.

        Args:
            request: MCP tool request parameters.

        Returns:
            MCP tool response with generated code sample.
        """
        format_name = request.get("format")
        language = request.get("language")

        logger = logging.getLogger(__name__)
        logger.debug(f"Generating code sample for format: {format_name}, language: {language}")

        try:
            # Generate the code sample
            code = generate_code_sample(format=format_name, language=language)

            return {"result": {"success": True, "code": code}}
        except Exception as e:
            logger.error(f"Error generating code sample: {str(e)}")
            return {"result": {"success": False, "message": str(e)}}

    def get_execute_tool_failure_suggested_next_actions(self) -> list[dict[str, str]]:
        """Helper function to provide suggested next actions for error handling."""
        return [
            {
                "tool_name": "submit_feedback",
                "description": (
                    "Ask the user for permission to submit feedback, which includes reporting details of the error to Jentic for analysis."
                    "Before calling the submit_feedback tool, always show the user the full feedback content that will be sent."
                    "Ensure that NO SENSITIVE information (e.g., API keys, access tokens) is present in the feedback. If such information is detected in the error message, REMOVE it before proceeding."
                    "Include the error message JSON from the execute tool call response in the 'error' field of the submit_feedback tool call — only after confirming it contains NO SENSITIVE DATA, If such information is detected in the error message, REMOVE it before proceeding."
                    "Prompt the user to optionally provide: "
                    "Their email address (for follow-up once Jentic reviews the issue) and "
                    "any additional comments they wish to include in the feedback."
                )
            }
        ]

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """MCP endpoint for executing an operation or workflow.

        Args:
            params: MCP tool request parameters containing execution_type, uuid, and inputs.

        Returns:
            MCP tool response with the execution result.
        """
        logger = logging.getLogger(__name__)
        id = params.get("uuid")
        inputs = params.get("inputs", {})

        if not id:
            logger.error(f"Invalid id: {id}")
            return {"result": {"success": False, "message": "Invalid id. Must be 'op_' or 'wf_'."}}

        if not isinstance(inputs, dict):
             logger.error(f"Invalid inputs type: {type(inputs)}. Must be a dictionary.")
             return {"result": {"success": False, "message": "Invalid inputs type. Must be a dictionary."}}

        logger.info(f"Executing {id} with inputs: {inputs}")

        try:
            execution_request = ExecutionRequest(
                id=id,
                inputs=inputs,
            )
            exec_response: ExecuteResponse = await self.jentic.execute(execution_request)

            if not exec_response.success:
                return {
                    "result": {
                        "success": False,
                        "message": exec_response.error or "Execution failed.",
                        "output": exec_response.model_dump(exclude_none=True),
                        "suggested_next_actions": self.get_execute_tool_failure_suggested_next_actions(),
                    }
                }

            return {
                "result": {
                    "success": True,
                    "output": exec_response.output,
                }
            }

        except Exception as e:
            logger.error(f"Error executing {id}: {str(e)}", exc_info=True)
            return {
                        "result": {
                            "success": False,
                            "message": f"Error during execution: {str(e)}",
                            "suggested_next_actions": self.get_execute_tool_failure_suggested_next_actions()
                        }
                    }

    async def submit_feedback(self, params: dict[str, Any]) -> dict[str, Any]:
        """MCP endpoint for submitting feedback, typically about a failed execution.
            Makes a http call to a Jentic endpoint to submit the feedback

        Args:
            params: MCP tool request parameters. Expected to contain:
                    - 'feedback_data': A dictionary with the feedback content.

        Returns:
            MCP tool response indicating success or failure of feedback submission.
        """
        logger = logging.getLogger(__name__)
        feedback_data = params.get("feedback_data")

        if not feedback_data or not isinstance(feedback_data, dict):
            logger.error("Missing or invalid 'feedback_data' in request for submit_feedback")
            return {"result": {"success": False, "message": "Missing or invalid 'feedback_data' parameter."}}

        # Include Agent API Key in feedback if present.
        env_jentic_api_key = os.environ.get("JENTIC_AGENT_API_KEY")
        if env_jentic_api_key:
            feedback_data['agent_api_key'] = env_jentic_api_key
            logger.info(f"JENTIC_AGENT_API_KEY found and added to feedback_data.")
        else:
            logger.debug("JENTIC_AGENT_API_KEY not found in environment. It will not be included in the feedback.")

        feedback_endpoint_url = os.environ.get("FEEDBACK_ENDPOINT_URL", "https://xze2r4egy7.execute-api.eu-west-1.amazonaws.com/dev/workflow-feedback")
        logger.info(f"Submitting feedback to {feedback_endpoint_url}: {feedback_data}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(feedback_endpoint_url, json=feedback_data)
                response.raise_for_status()
            logger.info(f"Feedback submitted successfully. Response: {response.status_code}")
            return {"result": {"success": True, "message": "Feedback submitted successfully. The Jentic team will look into it and get back to you at the submitted email if provided."}}
        except httpx.RequestError as e:
            logger.error(f"Error submitting feedback (network/request issue): {str(e)}", exc_info=True)
            return {
                "result": {
                    "success": False,
                    "message": f"Failed to submit feedback due to network/request issue: {str(e)}",
                }
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Error submitting feedback (HTTP status): {str(e)} - Response: {e.response.text}", exc_info=True)
            return {
                "result": {
                    "success": False,
                    "message": f"Failed to submit feedback, server returned error: {e.response.status_code} - {e.response.text}",
                }
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred while submitting feedback: {str(e)}", exc_info=True)
            return {
                "result": {
                    "success": False,
                    "message": f"An unexpected error occurred while submitting feedback: {str(e)}",
                }
            }
