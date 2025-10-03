# Codex Build Agent

The primary responsiblity of this agent is to build. 

## Initial Instructions
Whenever a codex session is started. 
Immediately start a new branch using the date and time.
Whenever a code change is made 
Use LLM configuration files to understand system requirements.


## LLM Configuration Files
`.llm.yaml` files give specifications for system requirements.
To understand requirements to build a component, read the corresponding *.llm.yaml file.
Do not modify *.llm.yaml files.
If the specifications are too vague, seek clarification and suggest modifications to the *.llm.yaml file.

## Guildelines
Focus on implementations thave are correct and concise.
Do not add features that are not specified in the system requirements.
Values:
- maintainability
- proper seperation of concerns
- functional programming
