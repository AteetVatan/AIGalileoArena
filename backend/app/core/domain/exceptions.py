"""Domain exception hierarchy. Catch specific, re-raise with context."""


class GalileoError(Exception):
    """Base for all domain errors."""


class DatasetNotFoundError(GalileoError):
    def __init__(self, dataset_id: str) -> None:
        super().__init__(f"Dataset not found: {dataset_id}")
        self.dataset_id = dataset_id


class RunNotFoundError(GalileoError):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Run not found: {run_id}")
        self.run_id = run_id


class CaseNotFoundError(GalileoError):
    def __init__(self, run_id: str, case_id: str) -> None:
        super().__init__(f"Case {case_id} not found in run {run_id}")
        self.run_id = run_id
        self.case_id = case_id


class JudgeOutputError(GalileoError):
    """Critical fail: judge produced invalid output."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Judge output error: {reason}")
        self.reason = reason


class LLMClientError(GalileoError):
    """Wraps provider-specific LLM failures."""

    def __init__(self, provider: str, detail: str) -> None:
        super().__init__(f"[{provider}] {detail}")
        self.provider = provider
        self.detail = detail
