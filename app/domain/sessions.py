from enum import StrEnum


class SessionStatus(StrEnum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


EDGES = {
    SessionStatus.DRAFT: {SessionStatus.SCHEDULED, SessionStatus.CANCELLED},
    SessionStatus.SCHEDULED: {SessionStatus.OPEN, SessionStatus.CANCELLED},
    SessionStatus.OPEN: {SessionStatus.CLOSED, SessionStatus.CANCELLED},
    SessionStatus.CLOSED: set(),
    SessionStatus.CANCELLED: set(),
}


def transition_session(current: str, target: str) -> SessionStatus:
    source = SessionStatus(current)
    destination = SessionStatus(target)
    if destination not in EDGES[source]:
        raise ValueError(f"Invalid session transition: {source} -> {destination}")
    return destination
