from google.adk.agents import SequentialAgent
from ..protected_query_builder_agent import protected_query_builder_agent
from ..query_executor_agent import query_executor_agent
# from ..human_response_agent import human_response_agent
# from ..response_insights_agent import response_insights_agent

full_pipeline_agent = SequentialAgent(
    name="full_pipeline_agent",
    sub_agents=[
        protected_query_builder_agent,
        query_executor_agent,
        # human_response_agent,
    #    response_insights_agent,

    ],
    description="Pipeline after intent OK: SQL builder -> executor."
)
