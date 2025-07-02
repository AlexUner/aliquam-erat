import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List


class LinguistWrapper:
    """Wrapper for github-linguist with Docker support."""

    def __init__(
        self,
        *,
        use_docker: bool = False,
        linguist_cmd: str = "github-linguist",
        docker_image: str = "linguist",
    ) -> None:
        self.use_docker = use_docker
        self.linguist_cmd = linguist_cmd
        self.docker_image = docker_image

    def analyze_zip(self, zip_path: str | os.PathLike) -> Dict[str, Dict[str, float | int]]:
        """
        Analyze programming languages in a ZIP archive.

        Returns:
            Dict mapping language names to {'percent': float, 'lines': int}
        """
        zip_path = Path(zip_path)
        if not zip_path.is_file():
            raise FileNotFoundError(f"File not found: {zip_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir_path)

            project_root = self._detect_project_root(tmpdir_path)
            self._init_git_repo(project_root)
            return self._collect_language_stats(project_root)

    def _collect_language_stats(self, repo_dir: Path) -> Dict[str, Dict[str, float | int]]:
        """Collect language statistics using linguist breakdown."""
        breakdown_data = self._run_linguist_breakdown(repo_dir)
        if not breakdown_data:
            raise RuntimeError("github-linguist returned empty result")

        total_bytes = sum(item.get("size", 0) for item in breakdown_data.values()) or 1
        stats = {}

        for language, info in breakdown_data.items():
            files = info.get("files", [])
            lines = sum(self._count_lines(repo_dir / f) for f in files)
            percent = round(info.get("size", 0) * 100.0 / total_bytes, 2)
            stats[language] = {"percent": percent, "lines": lines}

        return stats

    def _run_linguist_breakdown(self, repo_dir: Path) -> dict:
        """Run linguist with breakdown and JSON output."""
        output = self._execute_linguist(["--breakdown", "--json", "."], repo_dir)
        return json.loads(output)

    def _execute_linguist(self, args: List[str], repo_dir: Path) -> str:
        """Execute linguist command locally or in Docker container."""
        if self.use_docker:
            stat_info = os.stat(repo_dir)
            cmd = [
                "docker", "run", "--rm",
                "--user", f"{stat_info.st_uid}:{stat_info.st_gid}",
                "-v", f"{repo_dir}:/repo:ro",
                "-w", "/repo",
                self.docker_image,
                *args,
            ]
            cwd = None
        else:
            cmd = [self.linguist_cmd, *args]
            cwd = str(repo_dir)

        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            raise RuntimeError(
                f"github-linguist failed with code {result.returncode}: {result.stderr}"
            )

        return result.stdout

    @staticmethod
    def _count_lines(file_path: Path) -> int:
        """Count lines in file using binary mode for performance."""
        try:
            with file_path.open("rb") as f:
                return sum(chunk.count(b"\n") for chunk in iter(lambda: f.read(1 << 20), b""))
        except (IsADirectoryError, FileNotFoundError, PermissionError):
            return 0

    @staticmethod
    def _detect_project_root(extract_dir: Path) -> Path:
        """Detect the actual project root in extracted archive."""
        entries = [p for p in extract_dir.iterdir() if p.name != "__MACOSX"]
        subdirs = [p for p in entries if p.is_dir()]
        files = [p for p in entries if p.is_file()]

        # If single subdirectory with no files at root level, use subdirectory
        return subdirs[0] if len(subdirs) == 1 and not files else extract_dir

    @staticmethod
    def _init_git_repo(repo_path: Path) -> None:
        """Initialize temporary git repository for linguist."""
        def run_git(*cmd):
            subprocess.run(
                cmd,
                cwd=repo_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

        run_git("git", "init", "-q")
        run_git("git", "add", "-A")
        run_git(
            "git", "-c", "user.name=linguist", "-c", "user.email=linguist@example.com",
            "commit", "-m", "Initial commit", "-q"
        )