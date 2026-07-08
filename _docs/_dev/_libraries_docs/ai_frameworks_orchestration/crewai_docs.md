# CrewAI Documentation

## Overview
CrewAI is a Python framework for orchestrating autonomous AI agent teams that collaborate to solve complex tasks. It offers flexible tools, intelligent workflow orchestration, and sequential or hierarchical execution modes.

## Core Concepts

### Agents
Autonomous entities with:
- **Role**: Specific function (e.g., "Research Specialist")
- **Goal**: What the agent aims to achieve
- **Backstory**: Context that guides behavior
- **Tools**: Capabilities available to the agent
- **Delegation**: Ability to work with other agents

### Tasks
Work units assigned to agents:
- **Description**: What needs to be done
- **Expected Output**: Success criteria
- **Agent**: Who performs the task
- **Context**: Dependencies on other tasks
- **Output Files**: Where to save results

### Crews
Orchestrates agents and tasks:
- **Process**: Sequential or Hierarchical execution
- **Memory**: Conversation history retention
- **Planning**: Auto-generate execution plans

## Basic Usage

### Simple Crew

```python
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# Define agents
researcher = Agent(
    role='Market Research Analyst',
    goal='Provide up-to-date market analysis',
    backstory='Expert analyst with keen eye for trends',
    tools=[SerperDevTool()],
    verbose=True
)

writer = Agent(
    role='Content Writer',
    goal='Craft engaging content about AI',
    backstory='Skilled writer with passion for technology',
    verbose=True
)

# Define tasks
research_task = Task(
    description='Research latest AI industry trends',
    expected_output='Summary of top 3 developments with unique perspective',
    agent=researcher
)

write_task = Task(
    description='Write engaging blog post based on research',
    expected_output='4-paragraph blog post in markdown',
    agent=writer,
    output_file='blog-posts/new_post.md'
)

# Create and run crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    verbose=True,
    memory=True
)

result = crew.kickoff()
print(result.raw)
```

## Agent Configuration

### Agent with Tools

```python
from crewai import Agent
from crewai_tools import DirectoryReadTool, FileReadTool, SerperDevTool

analyst = Agent(
    role='Data Analyst',
    goal='Analyze data and provide insights',
    backstory='Experienced data scientist',
    tools=[DirectoryReadTool(), FileReadTool(), SerperDevTool()],
    allow_delegation=True,
    verbose=True
)
```

### Agent Collaboration

```python
# Agents can delegate and ask questions
researcher = Agent(
    role="Research Specialist",
    goal="Conduct thorough research",
    backstory="Expert researcher",
    allow_delegation=True,  # Can delegate to other agents
    verbose=True
)

writer = Agent(
    role="Content Writer",
    goal="Create engaging content",
    backstory="Skilled writer",
    allow_delegation=True,  # Can ask questions to other agents
    verbose=True
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    verbose=True
)
```

## Task Configuration

### Sequential Tasks

```python
task1 = Task(
    description="Research the latest trends",
    expected_output="Comprehensive research summary",
    agent=researcher
)

task2 = Task(
    description="Analyze the research findings",
    expected_output="Analysis report with recommendations",
    agent=analyst,
    context=[task1]  # Uses task1 output as context
)

task3 = Task(
    description="Write final report",
    expected_output="Publication-ready article",
    agent=writer,
    context=[task2]  # Uses task2 output as context
)
```

### Task with Structured Output

```python
from pydantic import BaseModel

class ResearchOutput(BaseModel):
    topic: str
    key_findings: list[str]
    confidence_score: float

structured_task = Task(
    description="Research {topic} and provide structured findings",
    expected_output="Structured research findings",
    agent=researcher,
    output_pydantic=ResearchOutput
)
```

## Crew Processes

### Sequential Process

```python
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,  # Tasks execute one after another
    verbose=True
)
```

### Hierarchical Process

```python
# Manager coordinates and delegates
manager = Agent(
    role="Project Manager",
    goal="Coordinate team efforts",
    backstory="Experienced manager skilled at delegation",
    allow_delegation=True,
    verbose=True
)

crew = Crew(
    agents=[manager, researcher, writer],
    tasks=[project_task],
    process=Process.hierarchical,  # Manager coordinates everything
    manager_llm="gpt-4o",
    verbose=True
)
```

## Memory & Knowledge

### Conversation Memory

```python
crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    memory=True,  # Enable conversation history
    verbose=True
)
```

### Knowledge Sources

```python
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.file_knowledge_source import FileKnowledgeSource

company_policy = StringKnowledgeSource(
    content="""
    Company Policy Guidelines:
    1. All reports must be reviewed by management
    2. Data privacy is paramount
    """
)

documentation = FileKnowledgeSource(
    file_path="./docs/product_manual.pdf"
)

crew = Crew(
    agents=[support_agent],
    tasks=[support_task],
    knowledge_sources=[company_policy, documentation],
    verbose=True
)
```

## Tools Integration

### Built-in Tools

```python
from crewai_tools import (
    DirectoryReadTool,
    FileReadTool,
    SerperDevTool,  # Web search
    WebsiteSearchTool
)

agent = Agent(
    role='Researcher',
    goal='Find information',
    tools=[
        DirectoryReadTool(directory='./data'),
        FileReadTool(),
        SerperDevTool(),
        WebsiteSearchTool()
    ]
)
```

### Custom Tools

```python
from crewai.tools import tool

@tool("multiply")
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

agent = Agent(
    role='Calculator',
    goal='Perform calculations',
    tools=[multiply]
)
```

## Multi-Agent Workflows

### Agent-to-Agent Communication

```python
coordinator = Agent(
    role="Coordinator",
    goal="Coordinate complex tasks",
    backstory="Expert at delegating",
    allow_delegation=True,
    a2a_agents=[specialist_agent],  # Can delegate to specialist
    verbose=True
)

task = Task(
    description="Analyze financial data",
    expected_output="Comprehensive analysis",
    agent=coordinator
)

crew = Crew(
    agents=[coordinator, specialist_agent],
    tasks=[task],
    verbose=True
)
```

## Structured Workflows

### CrewBase Pattern

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class ResearchCrew():
    """Research crew for AI analysis"""

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
```

### YAML Configuration

```yaml
# agents.yaml
researcher:
  role: "Research Specialist"
  goal: "Gather comprehensive information"
  backstory: "Expert researcher with deep analytical skills"

analyst:
  role: "Data Analyst"
  goal: "Analyze research findings"
  backstory: "Meticulous analyst"
```

```yaml
# tasks.yaml
research_task:
  description: >
    Research {topic} thoroughly
  expected_output: >
    A list of 10 bullet points
  agent: researcher

analysis_task:
  description: >
    Analyze the research findings
  expected_output: >
    Detailed analysis report
  agent: analyst
  output_file: report.md
```

## Advanced Features

### Planning Mode

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research, write],
    planning=True,  # Auto-generate execution plan
    verbose=True
)
```

### Reasoning Agents

```python
analyst = Agent(
    role="Data Analyst",
    goal="Analyze data and provide insights",
    backstory="Expert analyst",
    reasoning=True,  # Enable reasoning capabilities
    max_reasoning_attempts=3,
    verbose=True
)
```

### Multi-Modal Agents

```python
image_analyst = Agent(
    role="Image Analyst",
    goal="Analyze images and provide descriptions",
    backstory="Expert in visual analysis",
    multimodal=True,  # Can process images
    verbose=True
)

task = Task(
    description="Analyze the image at https://example.com/image.jpg",
    expected_output="Detailed image description",
    agent=image_analyst
)
```

## Execution

### Kickoff with Inputs

```python
crew = Crew(agents=[researcher], tasks=[research_task])

result = crew.kickoff(inputs={'topic': 'AI Agents', 'year': '2024'})

print(result.raw)        # Raw output
print(result.json_dict)  # JSON format
print(result.pydantic)   # Pydantic model (if configured)
```

### Async Execution

```python
result = await crew.kickoff_async(inputs={'topic': 'AI'})
```

## Best Practices

1. **Clear Roles**: Give agents specific, focused roles
2. **Detailed Goals**: Be explicit about what success looks like
3. **Rich Backstory**: Context helps guide agent behavior
4. **Tool Selection**: Only provide tools relevant to the role
5. **Task Descriptions**: Be specific about inputs and outputs
6. **Context Chaining**: Use context parameter to pass outputs between tasks
7. **Memory**: Enable for conversations requiring context
8. **Verbose Mode**: Use during development for debugging
9. **Output Files**: Specify for tasks that generate artifacts
10. **Error Handling**: Wrap crew execution in try-except blocks

## Installation

```bash
pip install crewai
pip install crewai-tools  # Additional tools
```

## Resources

- **Documentation**: https://docs.crewai.com/
- **GitHub**: https://github.com/crewaiinc/crewai
- **Examples**: https://github.com/crewaiinc/crewai-examples





