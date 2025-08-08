"""
Metadata manager for tracking run configuration and environment.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional


class MetadataManager:
    """Manages metadata for analysis runs including configuration, environment, and results."""

    def __init__(self):
        """Initialize metadata manager."""
        self.metadata = {
            "run_id": self._generate_run_id(),
            "timestamp": datetime.now().isoformat(),
            "environment": self._collect_environment(),
            "configuration": {},
            "parameters": {},
            "data_coverage": {},
            "results": {},
            "performance": {}
        }
        self.start_time = datetime.now()

    def _generate_run_id(self) -> str:
        """Generate a unique run ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(os.urandom(16)).hexdigest()[:8]
        return f"run_{timestamp}_{random_suffix}"

    def _collect_environment(self) -> Dict[str, Any]:
        """Collect environment information."""
        env_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "hostname": platform.node(),
            "processor": platform.processor(),
            "working_directory": os.getcwd(),
            "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
            "environment_variables": {
                "FMP_API_KEY": "***" if os.environ.get("FMP_API_KEY") else "not_set",
                "DEBUG": os.environ.get("DEBUG", "false")
            }
        }

        # Try to get git commit hash
        try:
            git_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            git_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            git_dirty = subprocess.call(
                ["git", "diff", "--quiet"],
                stderr=subprocess.DEVNULL
            ) != 0

            env_info["git"] = {
                "commit": git_hash,
                "branch": git_branch,
                "dirty": git_dirty
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            env_info["git"] = None

        return env_info

    def set_configuration(self, config: Dict[str, Any]) -> None:
        """
        Set the configuration used for the run.
        
        Args:
            config: Configuration dictionary
        """
        # Sanitize sensitive data
        sanitized_config = self._sanitize_config(config)
        self.metadata["configuration"] = sanitized_config

    def set_parameters(self, **kwargs) -> None:
        """
        Set run parameters.
        
        Args:
            **kwargs: Parameter key-value pairs
        """
        self.metadata["parameters"].update(kwargs)

    def set_data_coverage(self,
                         total_stocks: int,
                         filtered_stocks: int,
                         analyzed_stocks: int,
                         sectors: List[str],
                         date_range: Optional[Dict[str, str]] = None) -> None:
        """
        Set data coverage information.
        
        Args:
            total_stocks: Total number of stocks in universe
            filtered_stocks: Number of stocks after initial filters
            analyzed_stocks: Number of stocks fully analyzed
            sectors: List of sectors covered
            date_range: Date range of data used
        """
        self.metadata["data_coverage"] = {
            "total_stocks": total_stocks,
            "filtered_stocks": filtered_stocks,
            "analyzed_stocks": analyzed_stocks,
            "sectors": sectors,
            "date_range": date_range or {},
            "coverage_percentage": (analyzed_stocks / total_stocks * 100) if total_stocks > 0 else 0
        }

    def set_results(self,
                   qualifying_stocks: int,
                   top_stocks: List[Dict[str, Any]],
                   output_files: List[str]) -> None:
        """
        Set analysis results.
        
        Args:
            qualifying_stocks: Number of stocks that passed all criteria
            top_stocks: List of top stock information
            output_files: List of generated output files
        """
        self.metadata["results"] = {
            "qualifying_stocks": qualifying_stocks,
            "top_stocks": top_stocks,
            "output_files": output_files,
            "success": True
        }

    def set_performance_metrics(self,
                               api_calls: int = 0,
                               cache_hits: int = 0,
                               cache_misses: int = 0,
                               errors: int = 0) -> None:
        """
        Set performance metrics.
        
        Args:
            api_calls: Number of API calls made
            cache_hits: Number of cache hits
            cache_misses: Number of cache misses
            errors: Number of errors encountered
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        self.metadata["performance"] = {
            "duration_seconds": duration,
            "api_calls": api_calls,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_hit_rate": (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0,
            "errors": errors,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    def add_timing(self, stage: str, duration: float) -> None:
        """
        Add timing information for a specific stage.
        
        Args:
            stage: Name of the stage
            duration: Duration in seconds
        """
        if "timings" not in self.metadata["performance"]:
            self.metadata["performance"]["timings"] = {}
        self.metadata["performance"]["timings"][stage] = duration

    def add_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Add error information.
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        if "errors_detail" not in self.metadata:
            self.metadata["errors_detail"] = []

        self.metadata["errors_detail"].append({
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_message,
            "context": context or {}
        })

    def save(self, filepath: Optional[str] = None) -> str:
        """
        Save metadata to JSON file.
        
        Args:
            filepath: Optional custom filepath
            
        Returns:
            Path to saved file
        """
        if filepath is None:
            filepath = f"run_metadata_{self.metadata['run_id']}.json"

        with open(filepath, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)

        return filepath

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize configuration to remove sensitive data.
        
        Args:
            config: Original configuration
            
        Returns:
            Sanitized configuration
        """
        sanitized = config.copy()

        # List of keys to sanitize
        sensitive_keys = ['api_key', 'password', 'secret', 'token', 'credential']

        def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for key, value in d.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    result[key] = "***REDACTED***"
                elif isinstance(value, dict):
                    result[key] = sanitize_dict(value)
                else:
                    result[key] = value
            return result

        return sanitize_dict(sanitized)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the metadata.
        
        Returns:
            Summary dictionary
        """
        return {
            "run_id": self.metadata["run_id"],
            "timestamp": self.metadata["timestamp"],
            "duration": self.metadata.get("performance", {}).get("duration_seconds", 0),
            "total_stocks": self.metadata.get("data_coverage", {}).get("total_stocks", 0),
            "qualifying_stocks": self.metadata.get("results", {}).get("qualifying_stocks", 0),
            "success": self.metadata.get("results", {}).get("success", False)
        }


def create_metadata_manager() -> MetadataManager:
    """Create and return a new metadata manager instance."""
    return MetadataManager()
