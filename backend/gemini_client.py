"""Gemini 3 Pro API client for MigrateAI."""

import os
from typing import Optional, Dict, Any, List
from google import generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """Client for interacting with Gemini 3 Pro API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini client."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        thinking_budget: Optional[int] = None
    ) -> str:
        """
        Generate a response from Gemini 3 Pro.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools for function calling
            thinking_budget: Optional thinking budget for Thought Signatures
        
        Returns:
            Generated text response
        """
        generation_config = {
            "temperature": temperature,
        }
        
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        if thinking_budget:
            generation_config["thinking_budget"] = thinking_budget
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                system_instruction=system_instruction,
                tools=tools
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def transform_class_to_hooks(
        self,
        class_component_code: str,
        component_name: str,
        context: Optional[str] = None
    ) -> str:
        """
        Transform a React class component to functional component with hooks.
        
        Args:
            class_component_code: The source code of the class component
            component_name: Name of the component
            context: Optional context about the codebase
        
        Returns:
            Transformed functional component code
        """
        system_instruction = """You are an expert React developer specializing in migrating class components to functional components with hooks.

Transformation rules:
1. constructor + this.state → useState(initialValue)
2. componentDidMount → useEffect with empty deps array []
3. componentDidUpdate → useEffect with deps array
4. componentWillUnmount → useEffect cleanup function
5. this.setState → setState from useState
6. Class methods → regular functions or useCallback
7. this.refs / createRef → useRef

Preserve all functionality, props, and behavior. Return only the transformed code without explanations."""
        
        prompt = f"""Transform this React class component to a functional component with hooks:

Component: {component_name}

{context if context else ""}

```jsx
{class_component_code}
```

Return the complete transformed functional component code:"""
        
        return self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.3,  # Lower temperature for more deterministic transformations
            thinking_budget=10000  # Higher thinking budget for complex transformations
        )
    
    def analyze_codebase(
        self,
        file_tree: Dict[str, Any],
        file_contents: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyze codebase structure and dependencies.
        
        Args:
            file_tree: File tree structure
            file_contents: Dictionary mapping file paths to their contents
        
        Returns:
            Analysis results with component dependencies
        """
        system_instruction = """You are a code analysis expert. Analyze React codebases to identify:
1. Class components and their locations
2. Component dependencies and imports
3. State management patterns
4. Lifecycle method usage
5. Ref usage
6. Context usage

Return structured JSON analysis."""
        
        file_tree_str = self._format_file_tree(file_tree)
        file_contents_str = "\n\n".join([
            f"=== {path} ===\n{content}" 
            for path, content in list(file_contents.items())[:20]  # Limit to avoid token limits
        ])
        
        prompt = f"""Analyze this React codebase:

File Tree:
{file_tree_str}

Sample Files:
{file_contents_str}

Provide a JSON analysis with:
- class_components: list of class component file paths
- dependencies: mapping of components to their dependencies
- patterns: detected patterns (state management, lifecycle usage, etc.)"""
        
        response = self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.5,
            thinking_budget=5000
        )
        
        # Parse JSON from response (may need refinement based on actual response format)
        return self._parse_json_response(response)
    
    def _format_file_tree(self, file_tree: Dict[str, Any], indent: int = 0) -> str:
        """Format file tree dictionary as a string."""
        lines = []
        for key, value in file_tree.items():
            prefix = "  " * indent
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}/")
                lines.append(self._format_file_tree(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}")
        return "\n".join(lines)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from Gemini response (handles markdown code blocks)."""
        import json
        import re
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find JSON object directly
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Fallback: return raw response as dict
        return {"raw_response": response}
