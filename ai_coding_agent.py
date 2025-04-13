#!/usr/bin/env python3
"""
AI Coding Agent - A terminal-based assistant for full-stack development

This agent uses Google's Gemini Pro to:
1. Generate project structures
2. Write code for frontend and backend
3. Execute commands for dependency management and builds
4. Process follow-up requests with context awareness
"""

import os
import sys
import json
import base64
import argparse
import subprocess
from typing import Dict, List, Tuple, Optional

# Import Gemini API
from google import genai
from google.genai import types

class AICodingAgent:
    def __init__(self, api_key=None):
        # Configuration
        self.config_dir = os.path.expanduser("~/.ai_coding_agent")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.config = self.load_config()
        
        # Override API key if provided
        if api_key:
            self.config["api_key"] = api_key
            os.environ["GEMINI_API_KEY"] = api_key
        else:
            # Set environment variable from config
            os.environ["GEMINI_API_KEY"] = self.config["api_key"]
        
        # Initialize the Gemini client
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        
        # Project state
        self.current_project = None
        self.project_path = None
        self.file_cache = {}  # Cache file contents
        self.conversation_history = []
        
        # System prompt to guide the AI
        self.system_prompt = """
        You are an AI Coding Agent specialized in full-stack development through a terminal interface.
        
        Your capabilities:
        1. Create project structures with appropriate files and directories
        2. Write code for both frontend and backend
        3. Recommend and execute commands (pip install, npm install, etc.)
        4. Modify existing code based on new requirements
        
        When writing code or creating files, use these exact formats:
        - FILE: <filepath> - Followed by complete file content
        - DIR: <dirpath> - Create a directory
        - CMD: <command> - Execute a shell command
        
        Always provide complete file contents, not just snippets or changes.
        Explain your reasoning and approach clearly.
        """
    
    def load_config(self) -> Dict:
        """Load or create configuration file"""
        default_config = {
            "api_key": "",
            "model": "gemini-2.5-pro-preview-03-25",
            "temperature": 0.7,
            "workspace_path": os.path.expanduser("~/ai_coding_agent_workspace")
        }
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Load existing config or create default
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Update with any missing defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"Error loading config: {e}")
                return default_config
        else:
            # Create default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config at {self.config_file}")
            print("Please set your API key in this file or provide it as an argument.")
            return default_config
    
    def set_project(self, project_name: str) -> None:
        """Set the current project, creating it if needed"""
        self.current_project = project_name
        workspace_path = os.path.expanduser(self.config["workspace_path"])
        
        # Create workspace if it doesn't exist
        if not os.path.exists(workspace_path):
            os.makedirs(workspace_path)
        
        # Set and create project path
        self.project_path = os.path.join(workspace_path, project_name)
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)
        
        # Reset file cache
        self.file_cache = {}
        
        print(f"Project set: {project_name}")
        print(f"Path: {self.project_path}")
    
    def list_files(self, path: Optional[str] = None) -> List[str]:
        """List files in the project or a specific directory"""
        if not self.current_project:
            print("No project selected. Use !project <n> first.")
            return []
        
        # Determine the directory to list
        if path:
            dir_path = os.path.join(self.project_path, path)
        else:
            dir_path = self.project_path
        
        if not os.path.exists(dir_path):
            print(f"Directory not found: {path}")
            return []
        
        result = []
        for root, dirs, files in os.walk(dir_path):
            rel_path = os.path.relpath(root, self.project_path)
            for file in files:
                if rel_path == '.':
                    result.append(file)
                else:
                    result.append(os.path.join(rel_path, file))
        
        return sorted(result)
    
    def read_file(self, file_path: str) -> Optional[str]:
        """Read a file's content, with caching"""
        if not self.current_project:
            print("No project selected. Use !project <n> first.")
            return None
        
        full_path = os.path.join(self.project_path, file_path)
        
        # Return from cache if available
        if file_path in self.file_cache:
            return self.file_cache[file_path]
        
        # Read the file
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                self.file_cache[file_path] = content
                return content
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def write_file(self, file_path: str, content: str) -> bool:
        """Write content to a file, creating directories as needed"""
        if not self.current_project:
            print("No project selected. Use !project <n> first.")
            return False
        
        full_path = os.path.join(self.project_path, file_path)
        
        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update cache
            self.file_cache[file_path] = content
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    
    def create_directory(self, dir_path: str) -> bool:
        """Create a directory in the project"""
        if not self.current_project:
            print("No project selected. Use !project <n> first.")
            return False
        
        full_path = os.path.join(self.project_path, dir_path)
        
        try:
            os.makedirs(full_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    
    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """Execute a shell command in the project directory"""
        if not self.current_project:
            print("No project selected. Use !project <n> first.")
            return "", "No project selected", 1
        
        try:
            # Run the command in the project directory
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Get output
            stdout, stderr = process.communicate()
            return stdout, stderr, process.returncode
        except Exception as e:
            return "", str(e), 1
    
    def gather_project_context(self) -> str:
        """Gather current project context for the AI"""
        if not self.current_project:
            return "No active project."
        
        context = f"Current project: {self.current_project}\n\n"
        
        # Get file list
        files = self.list_files()
        if files:
            context += "Project files:\n"
            for file in files:
                context += f"- {file}\n"
        else:
            context += "Project is empty.\n"
        
        # Include content of key configuration files and small code files
        key_extensions = ['.json', '.py', '.js', '.html', '.css', '.md', '.txt', '.yaml', '.yml']
        key_filenames = ['package.json', 'requirements.txt', 'setup.py', 'README.md', 
                        '.gitignore', 'app.py', 'main.py', 'index.js', 'index.html']
        
        included_files = []
        
        # First include explicitly key files
        for filename in key_filenames:
            for file in files:
                if os.path.basename(file) == filename and file not in included_files:
                    included_files.append(file)
        
        # Then include small files with key extensions
        for file in files:
            if file not in included_files:
                ext = os.path.splitext(file)[1].lower()
                if ext in key_extensions:
                    file_path = os.path.join(self.project_path, file)
                    if os.path.getsize(file_path) < 10000:  # Only include files smaller than 10KB
                        included_files.append(file)
        
        # Limit to 10 files to avoid exceeding context window
        for file in included_files[:10]:
            content = self.read_file(file)
            if content:
                context += f"\nContent of {file}:\n```\n{content}\n```\n"
        
        return context
    
    def process_ai_response(self, response: str) -> None:
        """Process AI response and execute actions"""
        if not self.current_project:
            print("No project selected. Use !project <n> first.")
            return
        
        lines = response.split('\n')
        current_mode = None
        current_path = None
        current_content = []
        
        for line in lines:
            # Check for FILE marker
            if line.startswith("FILE: "):
                # Save previous file if there was one
                if current_mode == "FILE" and current_path and current_content:
                    content = '\n'.join(current_content)
                    if self.write_file(current_path, content):
                        print(f"✅ Created/Updated file: {current_path}")
                
                # Start new file
                current_mode = "FILE"
                current_path = line[6:].strip()
                current_content = []
            
            # Check for DIR marker
            elif line.startswith("DIR: "):
                # Save previous file if there was one
                if current_mode == "FILE" and current_path and current_content:
                    content = '\n'.join(current_content)
                    if self.write_file(current_path, content):
                        print(f"✅ Created/Updated file: {current_path}")
                
                # Create directory
                current_mode = None
                dir_path = line[5:].strip()
                if self.create_directory(dir_path):
                    print(f"✅ Created directory: {dir_path}")
                current_path = None
                current_content = []
            
            # Check for CMD marker
            elif line.startswith("CMD: "):
                # Save previous file if there was one
                if current_mode == "FILE" and current_path and current_content:
                    content = '\n'.join(current_content)
                    if self.write_file(current_path, content):
                        print(f"✅ Created/Updated file: {current_path}")
                
                # Execute command
                current_mode = None
                command = line[5:].strip()
                stdout, stderr, return_code = self.execute_command(command)
                
                if return_code == 0:
                    print(f"✅ Executed command: {command}")
                    if stdout:
                        print(f"Output: {stdout[:200]}{'...' if len(stdout) > 200 else ''}")
                else:
                    print(f"❌ Command failed: {command}")
                    if stderr:
                        print(f"Error: {stderr[:200]}{'...' if len(stderr) > 200 else ''}")
                
                current_path = None
                current_content = []
            
            # If in FILE mode, collect content
            elif current_mode == "FILE":
                current_content.append(line)
            
            # Just print other lines as the AI's explanation
            else:
                print(line)
        
        # Save the last file if there is one
        if current_mode == "FILE" and current_path and current_content:
            content = '\n'.join(current_content)
            if self.write_file(current_path, content):
                print(f"✅ Created/Updated file: {current_path}")
    
    def query_model(self, user_input: str) -> None:
        """Query Gemini with the user's input and project context"""
        if not self.current_project:
            print("No project selected. Use !project <n> first.")
            return
        
        # Gather context about the project
        context = self.gather_project_context()
        
        # Construct the full prompt with system prompt, context, and user input
        full_prompt = f"{self.system_prompt}\n\nUser request: {user_input}\n\nProject Context:\n{context}"
        
        print("Thinking...")
        
        try:
            # Set up Gemini request
            model = self.config["model"]
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=full_prompt),
                    ],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=self.config["temperature"],
                response_mime_type="text/plain",
            )
            
            # Collect chunks to create the full response
            response_text = ""
            print("\nAI Assistant Response:")
            
            # Use streaming to get the response
            for chunk in self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    response_text += chunk.text
                    # Print the chunk to show progress
                    print(chunk.text, end="")
                    sys.stdout.flush()
            
            print("\n")  # Add a newline after the streaming output
            
            # Process and execute actions in the response
            self.process_ai_response(response_text)
            
        except Exception as e:
            print(f"Error querying AI model: {e}")
    
    def run(self) -> None:
        """Main loop to interact with the user"""
        print("🤖 AI Coding Agent initialized")
        print("Type !help for available commands")
        
        while True:
            try:
                user_input = input("\n> ")
                
                # Exit commands
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Goodbye!")
                    break
                
                # Handle special commands (starting with !)
                if user_input.startswith("!"):
                    command_parts = user_input[1:].strip().split(maxsplit=1)
                    command = command_parts[0].lower()
                    
                    if command == "project":
                        if len(command_parts) < 2:
                            print("Usage: !project <project_name>")
                        else:
                            self.set_project(command_parts[1])
                    
                    elif command == "list":
                        files = self.list_files()
                        if files:
                            print("Project files:")
                            for file in files:
                                print(f"- {file}")
                        else:
                            print("No files in project.")
                    
                    elif command == "cat":
                        if len(command_parts) < 2:
                            print("Usage: !cat <file_path>")
                        else:
                            content = self.read_file(command_parts[1])
                            if content:
                                print(f"Content of {command_parts[1]}:")
                                print(content)
                    
                    elif command == "exec":
                        if len(command_parts) < 2:
                            print("Usage: !exec <shell_command>")
                        else:
                            stdout, stderr, code = self.execute_command(command_parts[1])
                            if code == 0:
                                print(f"Command executed successfully: {command_parts[1]}")
                                if stdout:
                                    print(stdout)
                            else:
                                print(f"Command failed with code {code}: {command_parts[1]}")
                                if stderr:
                                    print(stderr)
                    
                    elif command == "help":
                        print("""
Available commands:
!project <n>  - Set or create a project
!list            - List files in the current project
!cat <file>      - Show the content of a file
!exec <command>  - Execute a shell command
!help            - Show this help message

For any other input, the AI will process it as a coding task.
                        """)
                    
                    else:
                        print(f"Unknown command: {command}. Type !help for available commands.")
                
                # If not a special command, send to AI model
                else:
                    self.query_model(user_input)
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="AI Coding Agent - Terminal-based coding assistant")
    parser.add_argument("--api-key", help="API key for the Gemini API")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    agent = AICodingAgent(api_key=args.api_key)
    agent.run()