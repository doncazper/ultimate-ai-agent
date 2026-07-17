"""Exact human-commanded Matrix messaging contracts and native broker boundary."""

from .broker import (
    MatrixBrokerClient,
    MatrixBrokerConfig,
    MatrixBrokerInvocation,
    MatrixBrokerResponse,
    MatrixBrokerTransientInput,
)
from .availability import build_default_matrix_messaging_posture
from .constants import MATRIX_MESSAGING_LANES, MatrixMessagingOperation
from .contracts import (
    MatrixMessagingCommand,
    MatrixMessagingPosture,
    MatrixMessagingProposal,
    MatrixMessagingReadiness,
    build_matrix_messaging_command,
    build_matrix_messaging_proposal,
)
from .authority_surfaces import (
    capture_exact_matrix_messaging_approval,
    issue_exact_matrix_messaging_lease,
)
from .service import MatrixMessagingRuntime, execute_matrix_messaging_command

__all__ = [
    "MatrixBrokerClient",
    "MatrixBrokerConfig",
    "MatrixBrokerInvocation",
    "MatrixBrokerResponse",
    "MatrixBrokerTransientInput",
    "MATRIX_MESSAGING_LANES",
    "MatrixMessagingCommand",
    "MatrixMessagingOperation",
    "MatrixMessagingPosture",
    "MatrixMessagingProposal",
    "MatrixMessagingReadiness",
    "MatrixMessagingRuntime",
    "build_default_matrix_messaging_posture",
    "build_matrix_messaging_command",
    "build_matrix_messaging_proposal",
    "capture_exact_matrix_messaging_approval",
    "execute_matrix_messaging_command",
    "issue_exact_matrix_messaging_lease",
]
