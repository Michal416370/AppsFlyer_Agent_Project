"""
ADK entrypoint shim.

Exposes `root_agent` for `adk web` by importing
from the package-local flow manager implementation.
"""

from flow_manager_agent.agent import root_agent
