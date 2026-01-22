# MigrateAI

An autonomous codebase migration agent for the Gemini 3 hackathon that converts React class components to functional components with hooks.

## Overview

MigrateAI is a multi-agent system that autonomously migrates legacy React codebases. It analyzes, plans, executes, tests, and verifies migrations without human intervention, using Gemini 3's Thought Signatures to maintain context across long-running tasks.

## Architecture

The system consists of 8 specialized agents:

1. **Ingest Agent**: Clone repo, build file tree, detect tech stack
2. **Analyze Agent**: AST parsing, find class components, map dependencies
3. **Plan Agent**: Create migration DAG, order by dependencies
4. **Execute Agent**: Transform class to hooks using Gemini 3
5. **Test Agent**: Run npm test in Docker, handle failures
6. **Verify Agent**: Visual regression with Playwright screenshots
7. **Review Agent**: Self-review code quality
8. **Document Agent**: Generate PR descriptions, migration guides

## Tech Stack

- Backend: FastAPI + Python 3.11
- Frontend: React + TailwindCSS (simple dashboard)
- Orchestration: LangGraph for multi-agent coordination
- LLM: Google Gemini 3 Pro via AI Studio API
- Testing: Docker containers for sandboxed npm test execution
- State: SQLite for migration state persistence
- Git: GitPython for version control operations

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add your Gemini API key:
```bash
cp .env.example .env
```

3. Run the backend:
```bash
cd backend
uvicorn main:app --reload
```

## Migration Transformation Rules

- `constructor + this.state` → `useState(initialValue)`
- `componentDidMount` → `useEffect` with empty deps array
- `componentDidUpdate` → `useEffect` with deps array
- `componentWillUnmount` → `useEffect` cleanup function
- `this.setState` → `setState` from `useState`
- Class methods → regular functions or `useCallback`
- `this.refs / createRef` → `useRef`

## Demo Codebase

The `demo_codebase/` directory contains sample React class components for testing:
- Counter.jsx
- UserProfile.jsx
- Timer.jsx
- ContactForm.jsx
- DataFetcher.jsx
