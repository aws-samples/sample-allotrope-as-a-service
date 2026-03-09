# Quickstart Guide for Strands Agents

Strands Agents is a powerful framework for building AI agents that can interact with AWS services and perform complex tasks. This quickstart guide will help you get started with creating your first Strands agent.

## Prerequisites

- Python 3.10 or later
- AWS account configured with appropriate permissions
- Basic understanding of Python programming

Lets get started !


```python
# Install Strands using pip

!pip install strands-agents strands-agents-tools
```


## Creating Your First Agent

Lets get an overview of the agentic components needed.

### 1. Create a simple Agent:

This will create an agent with the default model provider, [Amazon Bedrock](https://aws.amazon.com/bedrock/), and the default model, Claude 3.7 Sonnet, in the region of your AWS setup. While the agent runs in the same local environment as it is being invoked, Amazon Bedrock models will run in an AWS account and your agent will invoke the model in the cloud account. The architecture looks as following:

<div style="text-align:center">
    <img src="images/simple_agent.png" width="75%" />
</div>


```python
import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow") 

from strands import Agent
# Initialize your agent
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",  # Optional: Specify the model ID
    system_prompt="You are a helpful assistant that provides concise responses."
)

# Send a message to the agent
response = agent("Hello! Tell me a joke.")
```

### 2. Add Tools to the Agent:

The [strands-agents-tools](https://github.com/strands-agents/tools) repository provides some in-built tools which you can import. You can also create custom tools using the `@tool` decorator. We can create agents with built-in and custom tools. For instance, adding the built-in tool of a calculator and a custom tool for getting the weather you get the following architecture:
<div style="text-align:center">
    <img src="images/agent_with_tools.png" width="75%" />
</div>

Implementing this architecture you have the following:


```python
from strands import Agent, tool
from strands_tools import calculator # Import the calculator tool

# Create a custom tool 
@tool
def weather():
    """ Get weather """ # Dummy implementation
    return "sunny"

agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",  # Optional: Specify the model ID
    tools=[calculator, weather],
    system_prompt="You're a helpful assistant. You can do simple math calculation, and tell the weather.")

response = agent("What is the weather today?")
print(response)
```

### Invoking tool directly

For some applications it is important to directly call the tool. For instance, you might want to debug the tool, pre-populate the agent knowledge with your customer's information or using a tool inside of another tool. In Strands you can do it using the ``tool`` method of your agent followed by the tool name


```python
# Alternatively, you can invoke the tool directly like so:
agent.tool.calculator(expression="sin(x)", mode="derive", wrt="x", order=2)
```


### 3. Changing the log level and format:

Strands SDK uses Python's standard `logging` module to provide visibility into its operations.

The Strands Agents SDK implements a straightforward logging approach:

1. **Module-level Loggers**: Each module in the SDK creates its own logger using logging.getLogger(__name__), following Python best practices for hierarchical logging.
2. **Root Logger**: All loggers in the SDK are children of the "strands" root logger, making it easy to configure logging for the entire SDK.
3. **Default Behavior**: By default, the SDK doesn't configure any handlers or log levels, allowing you to integrate it with your application's logging configuration.

To enable logging for the Strands Agents SDK, you can configure the **"strands"** logger. If you want to change the log level, for example during debugging, or modify the log format, you can set the logger configuration as follows:


```python
import logging
from strands import Agent

# Enables Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG) # or logging.INFO

# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

agent = Agent(model="us.anthropic.claude-3-7-sonnet-20250219-v1:0")  # Optional: Specify the model ID
agent("Hello!")
```


### 4. Model Provider

The default model provider is [Amazon Bedrock](https://aws.amazon.com/bedrock/) and the default model is Claude 3.7 Sonnet in the region of your current AWS environment

You can specify a different model in Amazon Bedrock providing the model ID string directly:


```python
from strands import Agent

agent = Agent(model="anthropic.claude-3-5-haiku-20241022-v1:0")
print(agent.model.config)
```


For more control over the model configuration, you can create a `BedrockModel` provider instance:


```python
import boto3
from strands import Agent
from strands.models import BedrockModel

# Create a BedrockModel
bedrock_model = BedrockModel(
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
    region_name='us-west-2',
    temperature=0.3,
)

agent = Agent(model=bedrock_model)
```


More details on the available model providers on the [Model Provider Quickstart page](https://strandsagents.com/0.1.x/user-guide/quickstart/#model-providers)


**Congratulations !! Now you have learned how to build a simple agent using Strands!!**

## [Optional] Lets Build a Task-Specific Agent - RecipeBot 🍽️

Lets create a practical example of a task-specific agent. We create a `RecipeBot` that recommends recipes and answers any cooking related questions. Lets dive in !!

Here's what we will create :

<div style="text-align:center">
    <img src="images/interactive_recipe_agent.png" width="75%" />
</div>


```python
# Install the required packages
%pip install ddgs # Also install strands-agents strands-agents-tools if you haven't already
```


```python
from strands import Agent, tool
from ddgs import DDGS
from ddgs.exceptions import RatelimitException, DDGSException
import logging

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

# Define a websearch tool
@tool
def websearch(keywords: str, region: str = "us-en", max_results: int | None = None) -> str:
    """Search the web to get updated information.
    Args:
        keywords (str): The search query keywords.
        region (str): The search region: wt-wt, us-en, uk-en, ru-ru, etc..
        max_results (int | None): The maximum number of results to return.
    Returns:
        List of dictionaries with search results.
    """
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        return results if results else "No results found."
    except RatelimitException:
        return "RatelimitException: Please try again after a short delay."
    except DDGSException as d:
        return f"DuckDuckGoSearchException: {d}"
    except Exception as e:
        return f"Exception: {e}"

```


```python
# Create a recipe assistant agent
recipe_agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",  # Optional: Specify the model ID
    system_prompt="""You are RecipeBot, a helpful cooking assistant.
    Help users find recipes based on ingredients and answer cooking questions.
    Use the websearch tool to find recipes when users mention ingredients or to
    look up cooking information.""",
    # Import the websearch tool we created above
    tools=[websearch],
)
```


```python
response = recipe_agent("Suggest a recipe with chicken and broccoli.")

# Other examples:
# response = recipe_agent("How do I cook quinoa?")
# response = recipe_agent("How can I substitute white wine in shrimp pasta?")
# response = recipe_agent("What are the health benefits of asparagus?")
print(response)
```

#### And that's it! We now have a running usecase agent with tools in just a few lines of code 🥳.

For more detailed quickstart guide, check out the [Strands documentation](https://strandsagents.com/0.1.x/user-guide/quickstart/).

### [Optional] Run RecipeBot via CLI: 
you can run the agent in interactive mode via the command line (for instance using the terminal on SageMaker Studio) through the python script provided in `02_simple_interactive_usecase/recipe_bot.py`. This allows you to interact with the agent in a more dynamic way, sending messages and receiving responses via the CLI.
Run these commands on a command line interface to run the agent in interactive mode:

```cli
cd samples/01-tutorials/01-fundamentals/01-first-agent/02-simple-interactive-usecase/
pip install -r requirements.txt
python recipe_bot.py
```

With this, you can talk to the bot via a command line interface(CLI).
