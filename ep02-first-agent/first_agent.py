"""
first_agent.py — EP02: Build Your First Azure AI Agent
Series: Agentic AI on Azure

The SAME agent you build in the Foundry portal, now in Python — including
Code Interpreter, so the Python agent matches the portal agent exactly.

Uses the modern Responses / Conversations API (azure-ai-projects 2.x).

Demonstrates:
  1. Create a versioned agent WITH the Code Interpreter tool
  2. A pure-compute question (agent writes + runs Python)
  3. CSV analysis — upload monthly_revenue.csv and analyze it
  4. A follow-up in the same conversation (history maintained)

Install:
  pip install --upgrade azure-ai-projects azure-identity python-dotenv
  az login

.env file (same folder):
  FOUNDRY_PROJECT_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>
  FOUNDRY_MODEL_NAME=gpt-4.1

Place monthly_revenue.csv in the same folder for the CSV analysis step.
"""

# import standard libraries
import os # for environment variables this is where we place libraries and packages 
from dotenv import load_dotenv # for loading .env file
load_dotenv() # load environment variables from .env file

from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, CodeInterpreterTool


def main() -> None:
    print("EP02 — Build Your First Azure AI Agent (Responses API)")
    print("Connecting to Microsoft Foundry...\n")

    # ── Step 1: Connect to the Foundry project ─────────────────────────────
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            credential=AzureCliCredential(), # uses Azure CLI credentials for authentication
               # active login session of the local Azure CLI
    )
    openai_client = project.get_openai_client() # gets an OpenAI client bound to the Foundry project, which is used to send messages to the agent and receive responses
    model = os.environ["FOUNDRY_MODEL_NAME"]
    m= project.deployments.get(model)
    print(m.type)
    
    # ── Step 2: Create the agent WITH Code Interpreter ─────────────────────
      # We connected to the project, now we are creating an agent with the Code Interpreter tool
    # This is the SAME agent you built in the portal: the same system prompt
    # (identity / capabilities / constraints) AND the same Code Interpreter
    # tool toggled on. CodeInterpreterTool() takes no arguments.
    agent = project.agents.create_version( # creates a new version of the agent in the Foundry project
        agent_name="first-agent-demo",
        definition=PromptAgentDefinition( # Built in class Links model and instructions to the agent 
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
            tools=[CodeInterpreterTool()], # tells the agent to use the Code Interpreter tool for data analysis tasks
        ),
    )
    print(f"Agent created: {agent.name}  (version {agent.version})")
    # print(f"View in portal: ai.azure.com -> your project -> Agents\n")

    agent_ref = {"type": "agent_reference", "name": agent.name, "version": agent.version} # reference to the created agent

      # ── Step 3: Get an OpenAI client bound to your Foundry project ──────────
       # This is the new pattern for Foundry Agents. The OpenAI client is used to
       # send messages to the agent and receive responses. It is bound to the Foundry project.
    conversation = openai_client.conversations.create()  # creates a new conversation thread for the agent to operate within

    # ── Step 5: CSV analysis — upload the file, analyze it ─────────────────
    # This mirrors the portal demo exactly: upload monthly_revenue.csv,
    # ask for the analysis, get real computed numbers back.
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
            extra_body={"agent_reference": agent_ref}, # tells the agent which agent to use for this conversation
            input=[{
                "type": "message", # the message type is a user message
                "role": "user", # the role is user, meaning the message is from the user to the agent
                "content": [
                    {"type": "input_text", "text": q1}, # the question to the agent
                    {"type": "input_file", "file_id": uploaded.id}, # the uploaded CSV file
                ],
            }],
        )
        _show_tools(r2)
        print(f"Agent: {r2.output_text}\n")
    else:
        print(f"(Skipping CSV demo — {csv_path} not found in this folder.)\n")

    # ── Step 6: A follow-up — history is maintained automatically ──────────
    print("=" * 60)
    print("DEMO 3 — Follow-up in the same conversation")
    print("=" * 60)
    q3 = "Based on that, write a one-sentence takeaway for an executive."
    print(f"User: {q3}\n")

    r3 = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": agent_ref},
        input=q3,
    )
    print(f"Agent: {r3.output_text}\n")

    print("-" * 60)
    print("Done. Same agent as the portal — now in Python.")
    print("-" * 60)


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