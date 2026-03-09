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