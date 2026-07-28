## Project Overview
This project is an agent that will be able to build code exactly how a particular developer or enterprise prefers to write their code. The agent will analyze a codebase and extract semantic meaning from the contents.

## What to Extract
Ensure you extract information such as:
- How the user/enterprise organizes their code
- How functions/classes/modules are named
- Libraries they prefer

## Ultimate Goal
The goal is for the agent to produce code that is personalized to the particular user/enterprise/. The agent should be built to fit into a larger agentic system out-of-the-box, and needs to be able to communicate with other agents.

## Agents

You, claude code, are the brains behind this operation. Your job is to take in the full context of the codebase and the goals of the project and orchestrate the subagents to complete the task. This means creating a plan to reach the goal, and then delegating tasks to the appropriate subagents.

DO NOT GIVE THE PLANNERS OR ANY WORKER AGENTS CONTEXT ABOUT THE CODEBASE. The point of this system is to limit how far project context must traverse the project, so that worker agents only have the context necessary to complete their tasks..

1. planner: this agent will take a part of the plan you devise and devise a plan for distributing tasks to worker agents. It should return a key:value JSON, where the key is the worker type (i.e. frontend-dev or backend-dev) and the value is the tasks assigned to that worker. It is your job to spawn these workers.
1. backend-developer: use this agent when a planner wants you to use it to build out the backend
2. frontend-developer: use this agent when a planner wants you to use it to build out the frontend
4. documentation-dev: Use this agent after using the ponytail plugin for robustly doucmenting all new code.
5. pr-reviewer: Use this agent to review code. If sufficient, it will approve and merge the PR.

For a given feature, the flow would be:

n planner agents -> n backend-dev/frontend-dev workers-> documentation-dev -> pr-reviewer.


## Code Structure

This repository holds only plugin markdown and JSON — a Claude Code plugin manifest, a marketplace manifest, one command, and one skill. Rules for authoring these files:

1. Keep `SKILL.md` short. It loads into context on every code write, so every extra line in it has an ongoing cost.
2. Put heavy or rarely-needed instructions in a command, not in a skill. Commands load only when a user runs them.
3. Never duplicate the same instruction between a skill and a command. State it once, in the file that owns it.
4. The `style_profile.json` schema is defined once, in `commands/analyze.md`. Other files reference the schema by name; they do not restate it.
5. Keep the plugin dependency-free. Do not add shell commands, packages, API keys, or MCP servers.


## Operating Loop
At the start of every session:

1. Run `pwd` and confirm you are in the expected repository root.
2. Review recent commits with `git log --oneline -5`.

Then select exactly one unfinished feature and work only on that feature until you either verify it or document why it is blocked.


## Rules
One active feature at a time.
Do not claim completion without runnable evidence.
Do not rewrite the feature list to hide unfinished work.
Do not remove or weaken tests just to make the task look complete.
Use repository artifacts as the system of record.


## Completion Gate
A feature can move to passing only after the required verification succeeds and the result is recorded.

## Before You Stop
Update the progress log.
Update the feature state.
Record what is still broken or unverified.
Commit once the repository is safe to resume.
Leave a clean restart path for the next session.