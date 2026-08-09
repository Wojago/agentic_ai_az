"""
first_agent.py — EP02: Build Your First Azure AI Agent
Series: Agentic AI on Azure

.env file (same folder):
  FOUNDRY_PROJECT_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>
  FOUNDRY_MODEL_NAME=gpt-4.1

Place sales_data.csv in the same folder for the CSV analysis step.
"""

# import standard libraries
import os 
from dotenv import load_dotenv 
load_dotenv() 

from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, CodeInterpreterTool


def main() -> None:
    print("EP02 — Build Your First Azure AI Agent (Responses API)")
    print("Connecting to Microsoft Foundry...\n")

    # ── Step 1: Connect to the Foundry project ─────────────────────────────
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            credential=AzureCliCredential(), 
   
    )
    openai_client = project.get_openai_client() 
    model = os.environ["FOUNDRY_MODEL_NAME"]
    m= project.deployments.get(model)
    print(m.type)
    
    # ── Step 2: Create the agent WITH Code Interpreter ─────────────────────

    agent = project.agents.create_version(
        agent_name="first-agent-demo",
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                # Identity
                "You are a data analysis specialist with expertise in "
                "identifying trends and summarizing datasets clearly. "
                # Capabilities
                "Analyze data, calculate statistics, and present findings "
                "with specific numbers. Write and run Python code when a "
                "calculation is needed. "
                # Constraints
                "Always cite the specific data points behind your conclusions. "
                "If a request is ambiguous, ask for clarification. "
                "Keep responses concise."
            ),
            tools=[CodeInterpreterTool()],
        ),
    )
    print(f"Agent created: {agent.name}  (version {agent.version})")

    agent_ref = {"type": "agent_reference", "name": agent.name, "version": agent.version} # reference to the created agent

      # ── Step 3: Get an OpenAI client bound to your Foundry project ──────────
    conversation = openai_client.conversations.create()  

    # ── Step 5: CSV analysis — upload the file, analyze it ────────────────
    csv_path = "sales_data.csv"
    if os.path.exists(csv_path):
        print("=" * 60)
        print("DEMO 2 — Code Interpreter: analyze an uploaded CSV")
        print("=" * 60)

        # Upload the file via the OpenAI files endpoint
        with open(csv_path, "rb") as f:
            uploaded = openai_client.files.create(file=f, purpose="assistants")
        print(f"Uploaded {csv_path} (file id: {uploaded.id})\n")

        q1 = ("Analyze the attached sales data. Calculate month-over-month "
              "growth, identify the top 3 revenue months, and name the top "
              "sales rep by total revenue.")
        print(f"User: {q1}\n")

        # Attach the file to the message so Code Interpreter can read it
        r2 = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": agent_ref}, 
            input=[{
                "type": "message", 
                "role": "user", 
                "content": [
                    {"type": "input_text", "text": q1}, 
                    {"type": "input_file", "file_id": uploaded.id}, 
                ],
            }],
        )
        _show_tools(r2)
        print(f"Agent: {r2.output_text}\n")
    else:
        print(f"(Skipping CSV demo — {csv_path} not found in this folder.)\n")

def _show_tools(response) -> None:
    """Print which tools the agent used, so the round-trip is visible."""
    used = []
    for item in response.output:
        itype = getattr(item, "type", "")
        if itype == "code_interpreter_call":
            used.append("code_interpreter")
    if used:
        print(f"  [tools used: {', '.join(used)}]")


if __name__ == "__main__":
    main()