"""Analyze Agent - AST parsing, find class components, map dependencies."""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..models import ClassComponent, ComponentType


class AnalyzeAgent:
    """Agent responsible for analyzing React components using AST."""
    
    def __init__(self):
        """Initialize the Analyze Agent."""
        pass
    
    def parse_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a JavaScript/JSX file using regex-based parsing.
        
        Note: Python's ast module doesn't support JavaScript.
        This is a simplified parser that uses regex to detect class components.
        For production, consider using a JavaScript parser like esprima or babel.
        
        Args:
            file_path: Path to the file to parse
        
        Returns:
            Parsed component information as dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._parse_jsx_content(content)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None
    
    def _parse_jsx_content(self, content: str) -> Dict[str, Any]:
        """
        Parse JSX content to extract component information.
        
        This is a simplified parser using regex. For production, use a proper JS parser.
        
        Args:
            content: JSX file content
        
        Returns:
            Dictionary with parsed information
        """
        result = {
            "type": ComponentType.UNKNOWN,
            "component_name": None,
            "is_class": False,
            "has_state": False,
            "has_lifecycle": False,
            "lifecycle_methods": [],
            "state_properties": [],
            "methods": [],
            "uses_refs": False,
            "uses_context": False,
            "imports": [],
            "exports": []
        }
        
        # Check if it's a class component
        class_pattern = r'class\s+(\w+)\s+extends\s+(?:React\.)?Component'
        class_match = re.search(class_pattern, content)
        
        if class_match:
            result["type"] = ComponentType.CLASS
            result["is_class"] = True
            result["component_name"] = class_match.group(1)
            
            # Check for state
            state_pattern = r'this\.state\s*=\s*\{([^}]+)\}'
            state_match = re.search(state_pattern, content, re.DOTALL)
            if state_match or 'this.state' in content:
                result["has_state"] = True
                if state_match:
                    state_content = state_match.group(1)
                    # Extract state properties
                    prop_pattern = r'(\w+)\s*:'
                    result["state_properties"] = re.findall(prop_pattern, state_content)
            
            # Check for lifecycle methods
            lifecycle_methods = [
                'componentDidMount',
                'componentDidUpdate',
                'componentWillUnmount',
                'componentWillMount',
                'componentWillReceiveProps',
                'shouldComponentUpdate',
                'getDerivedStateFromProps',
                'getSnapshotBeforeUpdate'
            ]
            
            for method in lifecycle_methods:
                method_pattern = rf'{method}\s*\([^)]*\)\s*\{{'
                if re.search(method_pattern, content):
                    result["lifecycle_methods"].append(method)
                    result["has_lifecycle"] = True
            
            # Extract all methods
            method_pattern = r'(\w+)\s*\([^)]*\)\s*\{'
            methods = re.findall(method_pattern, content)
            # Filter out lifecycle methods and constructor
            result["methods"] = [
                m for m in methods 
                if m not in lifecycle_methods and m != 'constructor' and m != 'render'
            ]
            
            # Check for refs
            if re.search(r'this\.refs|createRef|useRef', content):
                result["uses_refs"] = True
            
            # Check for context
            if re.search(r'this\.context|React\.createContext|useContext', content):
                result["uses_context"] = True
        
        # Extract imports
        import_pattern = r'import\s+(?:.*?\s+from\s+)?[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, content)
        result["imports"] = imports
        
        # Extract exports
        export_pattern = r'export\s+(?:default\s+)?(?:class|function|const)\s+(\w+)'
        export_match = re.search(export_pattern, content)
        if export_match:
            result["exports"] = [export_match.group(1)]
        
        return result
    
    def find_class_components(self, file_paths: List[str], repo_path: str) -> List[ClassComponent]:
        """
        Find all class components in the given files.
        
        Args:
            file_paths: List of file paths to analyze
            repo_path: Root path of the repository
        
        Returns:
            List of ClassComponent objects
        """
        class_components = []
        
        for file_path in file_paths:
            full_path = Path(repo_path) / file_path
            
            if not full_path.exists():
                continue
            
            parsed = self.parse_file(str(full_path))
            
            if parsed and parsed["is_class"]:
                # Extract dependencies from imports
                dependencies = []
                for imp in parsed["imports"]:
                    # Convert import paths to component names (simplified)
                    if imp.startswith('.'):
                        # Relative import - could be a local component
                        dependencies.append(imp)
                    elif not imp.startswith('react'):
                        # External import - might be a component
                        dependencies.append(imp)
                
                component = ClassComponent(
                    file_path=file_path,
                    component_name=parsed["component_name"],
                    has_state=parsed["has_state"],
                    has_lifecycle=parsed["has_lifecycle"],
                    lifecycle_methods=parsed["lifecycle_methods"],
                    dependencies=dependencies,
                    state_properties=parsed["state_properties"],
                    methods=parsed["methods"],
                    uses_refs=parsed["uses_refs"],
                    uses_context=parsed["uses_context"]
                )
                class_components.append(component)
        
        return class_components
    
    def map_dependencies(self, components: List[ClassComponent], repo_path: str) -> Dict[str, List[str]]:
        """
        Map dependencies between components.
        
        Args:
            components: List of class components
            repo_path: Root path of the repository
        
        Returns:
            Dictionary mapping component file paths to their dependencies
        """
        dependency_map = {}
        
        # Create a mapping of component names to file paths
        name_to_path = {comp.component_name: comp.file_path for comp in components}
        
        for component in components:
            component_deps = []
            full_path = Path(repo_path) / component.file_path
            
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find imports that match component names
                for dep_name, dep_path in name_to_path.items():
                    # Check if this component imports the dependency
                    import_pattern = rf'import\s+.*?\b{dep_name}\b.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
                    if re.search(import_pattern, content):
                        component_deps.append(dep_path)
                
                # Also check for relative imports
                relative_import_pattern = r'import\s+.*?\s+from\s+[\'"]\.([^\'"]+)[\'"]'
                relative_imports = re.findall(relative_import_pattern, content)
                for rel_import in relative_imports:
                    # Try to resolve relative path
                    resolved = self._resolve_relative_import(component.file_path, rel_import)
                    if resolved and resolved in [c.file_path for c in components]:
                        component_deps.append(resolved)
            
            dependency_map[component.file_path] = component_deps
        
        return dependency_map
    
    def _resolve_relative_import(self, current_file: str, import_path: str) -> Optional[str]:
        """
        Resolve a relative import path to an absolute file path.
        
        Args:
            current_file: Current file path
            import_path: Relative import path
        
        Returns:
            Resolved file path or None
        """
        current_dir = Path(current_file).parent
        resolved = (current_dir / import_path).resolve()
        
        # Try common extensions
        for ext in ['.jsx', '.js', '.tsx', '.ts']:
            if (resolved.parent / f"{resolved.name}{ext}").exists():
                return str((resolved.parent / f"{resolved.name}{ext}").relative_to(Path(current_file).parent.parent.parent))
        
        return None
    
    async def analyze(self, react_files: List[str], repo_path: str) -> Dict[str, Any]:
        """
        Main analyze method that performs all analysis tasks.
        
        Args:
            react_files: List of React file paths
            repo_path: Root path of the repository
        
        Returns:
            Dictionary with analysis results
        """
        # Find class components
        class_components = self.find_class_components(react_files, repo_path)
        
        # Map dependencies
        dependency_map = self.map_dependencies(class_components, repo_path)
        
        # Convert to dict and ensure file_path is a string
        class_components_dict = []
        for comp in class_components:
            comp_dict = comp.dict()
            # Ensure file_path is a string (not Path object)
            if hasattr(comp_dict.get("file_path"), '__str__') and not isinstance(comp_dict.get("file_path"), str):
                comp_dict["file_path"] = str(comp_dict["file_path"])
            class_components_dict.append(comp_dict)
        
        return {
            "class_components": class_components_dict,
            "dependency_map": dependency_map,
            "total_components": len(class_components),
            "total_files": len(react_files)
        }
