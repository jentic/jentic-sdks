import pytest
import os
from typing import Dict, Any
from pathlib import Path

from jentic.jentic import Jentic
from jentic.agent_runtime.tool_execution import WorkflowResult

def get_discord_operation_uuid(target_env: str, env_file_path: Path) -> str:
    """Get the Discord operation UUID from environment variables."""
    uuid = os.getenv("DISCORD_GET_MY_USER_OPERATION_UUID")
    if not uuid or "your_" in uuid:  # Check for placeholder
        pytest.fail(f"DISCORD_GET_MY_USER_OPERATION_UUID not set or is placeholder in {env_file_path} for {target_env} environment")
    return uuid

def get_discord_workflow_uuid(target_env: str, env_file_path: Path) -> str:
    """Get the Discord workflow UUID from environment variables."""
    uuid = os.getenv("DISCORD_GET_USER_DETAILS_WORKFLOW_UUID")
    if not uuid or "your_" in uuid:  # Check for placeholder
        pytest.fail(f"DISCORD_GET_USER_DETAILS_WORKFLOW_UUID not set or is placeholder in {env_file_path} for {target_env} environment")
    return uuid


@pytest.mark.asyncio
async def test_execute_discord_get_my_user_operation(target_env: str, env_file_path: Path):
    """Test executing a Discord read-only operation based on environment."""
    operation_uuid = get_discord_operation_uuid(target_env, env_file_path)
    jentic_client = Jentic()

    try:
        result = await jentic_client.execute_operation(
            operation_uuid=operation_uuid, inputs={}
        )
        assert isinstance(result, Dict), f"Expected result to be a Dict, got {type(result)}"
    except Exception as e:
        pytest.fail(f"execute_operation raised an exception: {e}")


@pytest.mark.asyncio
async def test_execute_discord_get_user_details_workflow(target_env: str, env_file_path: Path):
    """Test executing a Discord read-only workflow based on environment."""
    workflow_uuid = get_discord_workflow_uuid(target_env, env_file_path)
    jentic_client = Jentic()

    try:
        result = await jentic_client.execute_workflow(
            workflow_uuid=workflow_uuid, inputs={}
        )
        assert isinstance(result, WorkflowResult), f"Expected result to be a WorkflowResult, got {type(result)}"
    except Exception as e:
        pytest.fail(f"execute_workflow raised an exception: {e}")
