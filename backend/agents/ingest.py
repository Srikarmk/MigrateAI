"""Ingest Agent - Clone repo, build file tree, detect tech stack."""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from git import Repo
import json


class IngestAgent:
    """Agent responsible for ingesting the codebase."""
    
    def __init__(self, work_dir: Optional[str] = None):
        """
        Initialize the Ingest Agent.
        
        Args:
            work_dir: Working directory for cloning repos. If None, uses temp directory.
        """
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="migrateai_")
        self.repo_path: Optional[str] = None
    
    async def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """
        Clone a git repository.
        
        Args:
            repo_url: URL of the repository to clone
            branch: Branch to checkout (default: main)
        
        Returns:
            Path to the cloned repository
        """
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        self.repo_path = os.path.join(self.work_dir, repo_name)
        
        # Clone the repository
        if os.path.exists(self.repo_path):
            # If already exists, pull latest changes
            repo = Repo(self.repo_path)
            repo.remotes.origin.pull()
        else:
            repo = Repo.clone_from(repo_url, self.repo_path)
        
        # Checkout specified branch
        if branch != repo.active_branch.name:
            repo.git.checkout(branch)
        
        return self.repo_path
    
    def build_file_tree(self, root_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Build a nested dictionary representing the file tree.
        
        Args:
            root_path: Root path to build tree from. If None, uses repo_path.
        
        Returns:
            Nested dictionary representing the file structure
        """
        if root_path is None:
            root_path = self.repo_path
        
        if not root_path or not os.path.exists(root_path):
            raise ValueError(f"Invalid root path: {root_path}")
        
        tree = {}
        root = Path(root_path)
        
        # Ignore common directories
        ignore_dirs = {'.git', 'node_modules', '.next', 'dist', 'build', '__pycache__', '.venv', 'venv'}
        
        for item in root.rglob('*'):
            if item.is_dir():
                if item.name in ignore_dirs:
                    continue
                # Add directory to tree structure
                rel_path = item.relative_to(root)
                parts = rel_path.parts
                current = tree
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
            elif item.is_file():
                # Add file to tree structure
                rel_path = item.relative_to(root)
                parts = rel_path.parts
                current = tree
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = None  # Files are represented as None
        
        return tree
    
    def detect_tech_stack(self, root_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect the technology stack of the codebase.
        
        Args:
            root_path: Root path to analyze. If None, uses repo_path.
        
        Returns:
            Dictionary with detected tech stack information
        """
        if root_path is None:
            root_path = self.repo_path
        
        if not root_path or not os.path.exists(root_path):
            raise ValueError(f"Invalid root path: {root_path}")
        
        stack_info = {
            "package_manager": None,
            "framework": None,
            "has_typescript": False,
            "has_tests": False,
            "test_framework": None,
            "build_tool": None
        }
        
        root = Path(root_path)
        
        # Check for package.json
        package_json = root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    
                    # Detect package manager
                    if (root / "yarn.lock").exists():
                        stack_info["package_manager"] = "yarn"
                    elif (root / "pnpm-lock.yaml").exists():
                        stack_info["package_manager"] = "pnpm"
                    else:
                        stack_info["package_manager"] = "npm"
                    
                    # Detect framework
                    dependencies = package_data.get("dependencies", {})
                    dev_dependencies = package_data.get("devDependencies", {})
                    all_deps = {**dependencies, **dev_dependencies}
                    
                    if "react" in all_deps:
                        stack_info["framework"] = "react"
                    
                    # Detect TypeScript
                    if "typescript" in all_deps or (root / "tsconfig.json").exists():
                        stack_info["has_typescript"] = True
                    
                    # Detect test framework
                    if "jest" in all_deps or "vitest" in all_deps:
                        stack_info["has_tests"] = True
                        if "jest" in all_deps:
                            stack_info["test_framework"] = "jest"
                        elif "vitest" in all_deps:
                            stack_info["test_framework"] = "vitest"
                    
                    # Detect build tool
                    if "vite" in all_deps:
                        stack_info["build_tool"] = "vite"
                    elif "webpack" in all_deps:
                        stack_info["build_tool"] = "webpack"
                    elif "create-react-app" in all_deps or (root / "node_modules/.bin/react-scripts").exists():
                        stack_info["build_tool"] = "create-react-app"
            except Exception as e:
                print(f"Error reading package.json: {e}")
        
        return stack_info
    
    def get_react_files(self, root_path: Optional[str] = None) -> list[str]:
        """
        Get all React component files (.jsx, .js, .tsx, .ts).
        
        Args:
            root_path: Root path to search. If None, uses repo_path.
        
        Returns:
            List of file paths relative to root
        """
        if root_path is None:
            root_path = self.repo_path
        
        if not root_path or not os.path.exists(root_path):
            raise ValueError(f"Invalid root path: {root_path}")
        
        react_extensions = {'.jsx', '.js', '.tsx', '.ts'}
        react_files = []
        root = Path(root_path)
        
        ignore_dirs = {'.git', 'node_modules', '.next', 'dist', 'build', '__pycache__', '.venv', 'venv'}
        
        for file_path in root.rglob('*'):
            if file_path.is_file() and file_path.suffix in react_extensions:
                # Check if any parent directory is in ignore list
                if not any(part in ignore_dirs for part in file_path.parts):
                    rel_path = str(file_path.relative_to(root))
                    react_files.append(rel_path)
        
        return react_files
    
    async def ingest(self, repo_url: str, branch: str = "main") -> Dict[str, Any]:
        """
        Main ingest method that performs all ingestion tasks.
        
        Args:
            repo_url: URL of the repository to ingest
            branch: Branch to checkout
        
        Returns:
            Dictionary with ingestion results
        """
        # Clone repository
        repo_path = await self.clone_repository(repo_url, branch)
        
        # Build file tree
        file_tree = self.build_file_tree(repo_path)
        
        # Detect tech stack
        tech_stack = self.detect_tech_stack(repo_path)
        
        # Get React files
        react_files = self.get_react_files(repo_path)
        
        return {
            "repo_path": repo_path,
            "file_tree": file_tree,
            "tech_stack": tech_stack,
            "react_files": react_files
        }
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        # Note: In production, you might want to keep the repo for analysis
        # For now, we'll leave cleanup to the orchestrator
        pass
