class ServiceError(RuntimeError):
    pass

class ConflictError(ServiceError):
    pass