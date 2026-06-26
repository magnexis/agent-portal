from __future__ import annotations


class AgentPortalError(Exception):
    def __init__(
        self,
        message: str,
        *,
        module: str,
        likely_cause: str,
        suggested_fix: str,
        can_continue: bool,
    ) -> None:
        super().__init__(message)
        self.module = module
        self.likely_cause = likely_cause
        self.suggested_fix = suggested_fix
        self.can_continue = can_continue

    def to_dict(self) -> dict[str, object]:
        return {
            "message": str(self),
            "module": self.module,
            "likelyCause": self.likely_cause,
            "suggestedFix": self.suggested_fix,
            "canContinue": self.can_continue,
        }


class RuntimeStartupError(AgentPortalError):
    pass


class BrowserOperationError(AgentPortalError):
    pass


class PolicyBlockedError(AgentPortalError):
    pass
