"""Stable service-layer failures mapped by protocol adapters."""


class ServiceError(RuntimeError):
    code = "powerfarm.service_error"


class ValidationError(ServiceError):
    code = "powerfarm.validation_error"


class AuthorizationError(ServiceError):
    code = "powerfarm.authorization_error"


class NotFoundError(ServiceError):
    code = "powerfarm.not_found"


class ConflictError(ServiceError):
    code = "powerfarm.conflict"
