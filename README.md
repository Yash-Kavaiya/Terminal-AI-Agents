# Terminal-Based AI Coding Agent

A command-line tool that uses Google's Gemini Pro LLM to assist with full-stack development tasks.

## Features

- **Project Management**: Create, navigate, and manage project files
- **Code Generation**: Generate full project structures and code files
- **Context-Aware**: Understands existing code and responds to follow-up requests
- **Command Execution**: Run installation, build, and deployment commands

## Requirements

- Python 3.7+
- Google Gemini API key

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your API key:
   - When you first run the agent, it will create a config file at `~/.ai_coding_agent/config.json`
   - Add your Gemini API key to this file, or
   - Provide it as a command-line argument: `python ai_coding_agent.py --api-key YOUR_API_KEY`

## Usage

Run the agent:
```
python ai_coding_agent.py
```

### Commands

- `!project <name>` - Set or create a project
- `!list` - List files in the current project
- `!cat <file>` - Show the content of a file
- `!exec <command>` - Execute a shell command
- `!help` - Show help message

### Example Session

```
> !project flask_app

> Create a simple Flask app with a home page

[AI generates project files and explains its approach]
...

> Add a login functionality

[AI modifies existing code to include login features]
...

> !exec pip install -r requirements.txt

> !exec flask run
```

## How It Works

The agent:
1. Processes your natural language requests
2. Analyzes the current project state and files
3. Generates code and file structures
4. Executes commands as needed
5. Maintains context for follow-up requests

The AI formats its response with special markers:
- `FILE: <filepath>` - Indicates file content to write
- `DIR: <dirpath>` - Creates a directory
- `CMD: <command>` - Executes a shell command