import os
import platform
from pathlib import Path
from typing import List, Set

class DiscoveryService:
    """Smart discovery for developer history and projects."""

    COMMON_PROJECT_MARKERS = {".git", ".vscode", "package.json", "requirements.txt", "pom.xml", "build.gradle"}
    SKIP_DIRS = {"node_modules", ".git", ".next", "__pycache__", ".venv", "venv", "dist", "build"}

    @classmethod
    def get_user_home(cls) -> Path:
        return Path(os.path.expanduser("~"))

    @classmethod
    def find_shell_history(cls) -> List[Path]:
        """Locate shell history files."""
        home = cls.get_user_home()
        candidates = []
        
        system = platform.system()
        if system == "Windows":
            # PowerShell History
            ps_hist = home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt"
            if ps_hist.exists():
                candidates.append(ps_hist)
        else:
            # Bash/Zsh History
            for name in [".bash_history", ".zsh_history", ".python_history"]:
                f = home / name
                if f.exists():
                    candidates.append(f)
        
        return candidates

    @classmethod
    def find_potential_projects(cls, start_path: Path, max_depth: int = 3) -> Set[Path]:
        """Crawl a directory to find project roots."""
        project_roots = set()
        
        def _crawl(path: Path, depth: int):
            if depth > max_depth: return
            try:
                # Check for markers
                items = {item.name for item in path.iterdir()}
                if any(marker in items for marker in cls.COMMON_PROJECT_MARKERS):
                    project_roots.add(path)
                    return # Found a project, stop nesting here

                # Recurse
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith(".") and item.name not in cls.SKIP_DIRS:
                        _crawl(item, depth + 1)
            except (PermissionError, FileNotFoundError):
                pass

        _crawl(start_path, 0)
        return project_roots

    @classmethod
    def get_starter_paths(cls) -> List[Path]:
        """Get a list of all high-value paths to start ingestion."""
        all_paths = set(cls.find_shell_history())
        
        # 2. Common Dev Dirs
        home = cls.get_user_home()
        dev_dirs = ["Documents", "Desktop", "projects", "Source", "Repos", "Work"]
        for d in dev_dirs:
            p = home / d
            if p.exists():
                all_paths.update(cls.find_potential_projects(p))
                
        return sorted(list(all_paths))
