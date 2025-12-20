from pathlib import Path


class Profile:
    @staticmethod
    def get_project_root() -> Path:
        current_path = Path(__file__)

        for parent in current_path.parents:
            if (parent / "config.yaml").exists():
                return parent

        return current_path.parent.parent