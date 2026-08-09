
# install packages and import libraries 
import os 
from dotenv import load_dotenv 
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import CodeInterpreterTool
from azure.identity import DefaultAzureCredential
import pathlib
load_dotenv() 



# Connect to Microsoft Foundry using the project endpoint from .env
agents_client = AgentsClient(
    endpoint=os.environ['FOUNDRY_PROJECT_ENDPOINT'],
    credential=DefaultAzureCredential()
)

print('Connected to Microsoft Foundry project')

# Define Code Interpreter as the agent's tool
code_interpreter = CodeInterpreterTool() 

agent = agents_client.create_agent(
    model=os.environ['FOUNDRY_MODEL_NAME'],
    name='data-analyst-agent-sdk',
    instructions=(
        'You are a data analysis specialist with expertise in identifying '
        'trends and summarizing datasets clearly. '
        'Always cite the specific data points behind your conclusions. '
        'Lead with the most important finding.'
    ),
    tools=code_interpreter.definitions,
    tool_resources=code_interpreter.resources, 
)
print(f'Agent created: {agent.id}')


# Upload the data file for Code Interpreter to access
uploaded_file = agents_client.files.upload_and_poll(
    file_path='sales_data.csv', 
    purpose='assistants' 
)
print(f'File uploaded: {uploaded_file.id}')

# Create a conversation thread
thread = agents_client.threads.create() #
print(f'Thread created: {thread.id}')

# Add the user message to the thread
agents_client.messages.create(
    thread_id=thread.id,
    role='user',
    content=(
        'Analyze this sales data. Calculate month-over-month growth rates, '
        'identify the top 3 performing months, find the worst performing month, '
        'and give me a one-sentence summary of the overall trend.'
    ),
    attachments=[{ 
        'file_id': uploaded_file.id,
        'tools': [{'type': 'code_interpreter'}] 
    }]
)

# Run the agent — create_and_process handles the entire loop
run = agents_client.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id 
)
print(f'Run status: {run.status}')

# Retrieve the agent's response messages
messages = agents_client.messages.list(thread_id=thread.id)

print('\n--- Agent Response ---')
for msg in messages:
    if msg.role == 'assistant':
        for block in msg.content:
            if hasattr(block, 'text'):
                print(block.text.value)
        break

# Optional: clean up the agent when done
# agents_client.delete_agent(agent.id) 
