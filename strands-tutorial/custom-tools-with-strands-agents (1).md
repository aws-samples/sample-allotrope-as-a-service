# Adding custom tools to your Strands Agents

## Overview
In this example we will guide you through the different ways to create custom tools using Strands Agents. We will build a personal assistant use case that connects with a local SQLite database to perform data tasks. As a bonus, we will also guide you through the usage of the reasoning capabilities on Claude Sonnet 3.7 using the `thinking` field of the `BedrockModel` class

## Agent Details
<div style="float: left; margin-right: 20px;">
    
|Feature             |Description                                        |
|--------------------|---------------------------------------------------|
|Native tools used   |current_time, calculator                           |
|Custom tools created|create_appointment, list_appointments              |
|Agent Structure     |Single agent architecture                          |

</div>


## Architecture

<div style="text-align:left">
    <img src="images/architecture.png" width="85%" />
</div>

## Key Features
* **Single agent architecture**: this example creates a single agent that interacts with built-in and custom tools
* **Built-in tools**: learn how to use Strands Agent's tools
* **Custom tools**: lean how to create your own tools
* **Bedrock Model as underlying LLM**: Used Anthropic Claude 3.7 from Amazon Bedrock as the underlying LLM model

## Setup and prerequisites

### Prerequisites
* Python 3.10+
* AWS account
* Anthropic Claude 3.7 enabled on Amazon Bedrock, [guide](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
* IAM role with permissions to create Amazon Bedrock Knowledge Base, Amazon S3 bucket and Amazon DynamoDB

Let's now install the requirement packages for our Strands Agent


```python
# installing pre-requisites
!pip install -r requirements.txt
```

### Importing dependency packages

Now let's import the dependency packages


```python
import json
import sqlite3
import uuid
from datetime import datetime

from strands import Agent, tool
from strands.models import BedrockModel
```

## Defining custom tools
Next let's define custom tools to interact with a local SQLite database:
* **create_appointment**: create a new personal appointment with unique id, date, location, title and description 
* **list_appointment**: list all available appointments
* **update_appointments**: update an appointment based on the appointment id

### Defining tools in the same file of your agent

There are multiple ways to define tools with the Strands Agents SDK. The first one is to add a `@tool` decorator to your function and provide the documentation to it. In this case, Strands Agents will use the function documentation, typing and arguments to provide the tools to your agent. In this case, you can even define the tool in the same file as your agent


```python
@tool
def create_appointment(date: str, location: str, title: str, description: str) -> str:
    """
    Create a new personal appointment in the database.

    Args:
        date (str): Date and time of the appointment (format: YYYY-MM-DD HH:MM).
        location (str): Location of the appointment.
        title (str): Title of the appointment.
        description (str): Description of the appointment.

    Returns:
        str: The ID of the newly created appointment.

    Raises:
        ValueError: If the date format is invalid.
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD HH:MM'")

    # Generate a unique ID
    appointment_id = str(uuid.uuid4())

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    # Create the appointments table if it doesn't exist
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        date TEXT,
        location TEXT,
        title TEXT,
        description TEXT
    )
    """
    )

    cursor.execute(
        "INSERT INTO appointments (id, date, location, title, description) VALUES (?, ?, ?, ?, ?)",
        (appointment_id, date, location, title, description),
    )

    conn.commit()
    conn.close()
    return f"Appointment with id {appointment_id} created"
```

### Tool definition with Module-Based Approach

You can also define your tools as a standalone file and import it to your agent. In this case you can still use the decorator approach or you could also define your function using a TOOL_SPEC dictionary. The formating is similar to the one used by the [Amazon Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use-examples.html) for tool usage. In this case you are more flexible to define the required parameters as well as the return of success and error executions and TOOL_SPEC definitions will work in this case.

#### Decorator approach

When defining your tool using a decorator in a standalone file, your process is very similar to the one in the same file as your agent, but you will need to import or agent tool later on.


```python
%%writefile list_appointments.py
import json
import sqlite3
import os
from strands import tool

@tool
def list_appointments() -> str:
    """
    List all available appointments from the database.
    
    Returns:
        str: the appointments available 
    """
    # Check if database exists
    if not os.path.exists('appointments.db'):
        return "No appointment available"
    
    conn = sqlite3.connect('appointments.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Check if the appointments table exists
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        if not cursor.fetchone():
            conn.close()
            return "No appointment available"
        
        cursor.execute("SELECT * FROM appointments ORDER BY date")
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        appointments = []
        for row in rows:
            appointment = {
                'id': row['id'],
                'date': row['date'],
                'location': row['location'],
                'title': row['title'],
                'description': row['description']
            }
            appointments.append(appointment)
        
        conn.close()
        return json.dumps(appointments)
    
    except sqlite3.Error:
        conn.close()
        return []

```

#### TOOL_SPEC approach

Alternativelly, you can use the TOOL_SPEC approach when defining your tool


```python
%%writefile update_appointment.py
import sqlite3
from datetime import datetime
import os
from strands.types.tools import ToolResult, ToolUse
from typing import Any

TOOL_SPEC = {
    "name": "update_appointment",
    "description": "Update an appointment based on the appointment ID.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "The appointment id."
                },
                "date": {
                    "type": "string",
                    "description": "Date and time of the appointment (format: YYYY-MM-DD HH:MM)."
                },
                "location": {
                    "type": "string",
                    "description": "Location of the appointment."
                },
                "title": {
                    "type": "string",
                    "description": "Title of the appointment."
                },
                "description": {
                    "type": "string",
                    "description": "Description of the appointment."
                }
            },
            "required": ["appointment_id"]
        }
    }
}
# Function name must match tool name
def update_appointment(tool: ToolUse, **kwargs: Any) -> ToolResult:
    tool_use_id = tool["toolUseId"]
    appointment_id = tool["input"]["appointment_id"]
    if "date" in tool["input"]:
        date = tool["input"]["date"]
    else:
        date = None
    if "location" in tool["input"]:
        location = tool["input"]["location"]
    else:
        location = None
    if "title" in tool["input"]:
        title = tool["input"]["title"]
    else:
        title = None
    if "description" in tool["input"]:
        description = tool["input"]["description"]
    else:
        description = None
        
    # Check if database exists
    if not os.path.exists('appointments.db'): 
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Appointment {appointment_id} does not exist"}]
        } 
    
    # Check if appointment exists
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    # Check if the appointments table exists
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        if not cursor.fetchone():
            conn.close()
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Appointments table does not exist"}]
            }
        
        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        appointment = cursor.fetchone()
        
        if not appointment:
            conn.close()
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Appointment {appointment_id} does not exist"}]
            }
        
        # Validate date format if provided
        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d %H:%M')
            except ValueError:
                conn.close()
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": "Date must be in format 'YYYY-MM-DD HH:MM'"}]
                }
        
        # Build update query
        update_fields = []
        params = []
        
        if date:
            update_fields.append("date = ?")
            params.append(date)
        
        if location:
            update_fields.append("location = ?")
            params.append(location)
        
        if title:
            update_fields.append("title = ?")
            params.append(title)
        
        if description:
            update_fields.append("description = ?")
            params.append(description)
        
        # If no fields to update
        if not update_fields:
            conn.close()
            return {
                "toolUseId": tool_use_id,
                "status": "success",
                "content": [{"text": "No need to update your appointment, you are all set!"}]
            }
        
        # Complete the query
        query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE id = ?"
        params.append(appointment_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": f"Appointment {appointment_id} updated with success"}]
        }
    
    except sqlite3.Error as e:
        conn.close()
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": str(e)}]
        }

```

let's now import `list_appointments` and `update_appointment` as a tool


```python
import list_appointments
import update_appointment
```

## Creating Agent

Now that we have created our custom tools, let's define our first agent. To do so, we need to create a system prompt that defines what the agent should and should not do. We will then define our agent's underlying LLM model and we will provide it with built-in and custom tools. 

#### Setting agent system prompt
In the system prompt we will define the instructions for our agent


```python
system_prompt = """You are a helpful personal assistant that specializes in managing my appointments and calendar. 
You have access to appointment management tools, a calculator, and can check the current time to help me organize my schedule effectively. 
Always provide the appointment id so that I can update it if required"""
```

#### Defining agent underlying LLM model

Next let's define our agent underlying model. Strands Agents natively integrate with Amazon Bedrock models, and provides the ability to configure how the model is called. Below, you can see a simple initialization of a `BedrockModel` provider, with some of the optional configurations commented out. You can learn more about configuration options, and default values, at [Strands Agents Bedrock Model Provider documentation](https://strandsagents.com/0.1.x/user-guide/concepts/model-providers/amazon-bedrock/). For our example, we will use the `Anthropic Claude 3.7 Sonnet` model from Bedrock.


```python
model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    # region_name="us-east-1",
    # boto_client_config=Config(
    #    read_timeout=900,
    #    connect_timeout=900,
    #    retries=dict(max_attempts=3, mode="adaptive"),
    # ),
    # temperature=0.9,
    # max_tokens=2048,
)
```

#### Import built-in tools

The next step to build our agent is to import our Strands Agents built-in tools. Strands Agents provides a set of commonly used built-in tools in the optional package `strands-tools`. You have tools for RAG, memory, file operations, code interpretation and others available in this repo. For our example we will use the `current_time` tool to provide our agent with the information about the current time and the `calculator` tool to do some math


```python
from strands_tools import calculator, current_time
```

#### Defining Agent

Now that we have all the required information available, let's define our agent


```python
agent = Agent(
    model=model,
    system_prompt=system_prompt,
    tools=[
        current_time,
        calculator,
        create_appointment,
        list_appointments,
        update_appointment,
    ],
)
```

## Invoking agent

Let's now invoke our restaurant agent with a greeting and analyse its results


```python
results = agent("How much is 2+2?")
```

#### Analysing the agent's results

Nice! We've invoked our agent for the first time! Let's now explore the results object. First thing we can see is the messages being exchanged by the agent in the agent's object


```python
agent.messages
```

Next we can take a look at the usage of our agent for the last query by analysing the result `metrics`


```python
results.metrics
```

#### Invoking agent with follow up question
Ok, let's now make an appointment for tomorrow


```python
results = agent(
    "Book 'Agent fun' for tomorrow 3pm in NYC. This meeting will discuss all the fun things that an agent can do"
)
```

#### Updating appointment

Let's now update this appointment


```python
results = agent("Oh no! My bad, 'Agent fun' is actually happening in DC")
```

#### Analysing the agent's results
Let's look at the agent messages and result metrics again


```python
agent.messages
```


```python
results.metrics
```

#### Checking tool usage from messages

Let's deep-dive into the tool usage in the messages dictionary. Later on we will show case how to observe and evaluate your agent's behavior, but this is the first step in this direction


```python
for m in agent.messages:
    for content in m["content"]:
        if "toolUse" in content:
            print("Tool Use:")
            tool_use = content["toolUse"]
            print("\tToolUseId: ", tool_use["toolUseId"])
            print("\tname: ", tool_use["name"])
            print("\tinput: ", tool_use["input"])
        if "toolResult" in content:
            print("Tool Result:")
            tool_result = m["content"][0]["toolResult"]
            print("\tToolUseId: ", tool_result["toolUseId"])
            print("\tStatus: ", tool_result["status"])
            print("\tContent: ", tool_result["content"])
            print("=======================")
```

### Validating that the action was performed correctly
Let's now check our database to confirm that the operations where done correctly. The `Agent` class has the ability for directly calling tools the agent was initialized with by calling `agent.tool.<tool_name>(<tool_params>)`. Direct tool calls are great for giving the agent information from a tool without needing the agent to invoke that tool itself. We can use this direct tool invocation to list the current appointments:


```python
list_appointments_result = agent.tool.list_appointments()
print(json.dumps(list_appointments_result, indent=2))
```

We can see that the result of executing the tool is in the ToolResult format, including a `toolUseId`, an execution `status`, and the `content` of the response. We can better visualize the tool's result like this:


```python
list_appointments_result_text_content = list_appointments_result["content"][0]["text"]
print(json.dumps(json.loads(list_appointments_result_text_content), indent=2))
```

Finally, when executing tools using direct tool invocation, the agent records these executions in its messages history. By default this is enabled, but can be disabled with the `record_direct_tool_call` boolean flag attribute on the `Agent` class.


```python
current_time_result = agent.tool.current_time()
print("Current Time direct tool call result:")
print(current_time_result)
current_time_direct_tool_messages = agent.messages[-4:]
print("Current Time direct tool call messages:")
print(current_time_direct_tool_messages)

agent.record_direct_tool_call = False # Set the record_direct_tool_call to False
agent.tool.list_appointments()
after_disable_record_messages = agent.messages[-4:]
print("After disabling record direct tool call messages, history should not have changed:")
print(current_time_direct_tool_messages == after_disable_record_messages)
```

## Extension: Extended Thinking
 
Extended thinking enables supported Claude-family models the ability to leverage enhanced reasoning capabilities for complex tasks, providing transparent step-by-step thought processes before delivering final answers. To enable thinking, you can include the configuration below when configuring your Bedrock ModelProvider. You can learn more at [AWS's documentation on Extended Thinking](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html).


```python
thinking_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    additional_request_fields={
        "thinking": {
            "type": "enabled",
            "budget_tokens": 2048,
        }
    },
)
```

After defining the `thinking_model`, you can create and invoke a new `thinking_agent`:


```python
thinking_system_prompt = """You are a helpful personal assistant that specializes in managing my appointments and calendar. 
You have access to appointment management tools, a calculator, and can check the current time to help me organize my schedule effectively. 
You think through your problem, step by step, to come up with an answer.
Always provide the appointment id so that I can update it if required"""

thinking_agent = Agent(
    model=thinking_model,
    system_prompt=thinking_system_prompt,
    tools=[
        current_time,
        calculator,
        create_appointment,
        list_appointments,
        update_appointment,
    ],
)

thinking_result = thinking_agent("I want to add a new appointment for tomorrow at 2pm")
```

We can better analyze the extended thinking capabilities by printing out the agent's messages. Extended thinking is represented as `reasoningContent` blocks in the response from the agent.


```python
thinking_agent.messages
```

## Great work !
See you in the next module. :)
