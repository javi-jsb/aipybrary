class MemberNotFoundError(Exception):
    pass


class MemberSuspendedError(Exception):
    pass


class BookCopyNotFoundError(Exception):
    pass


class BookCopyNotAvailableError(Exception):
    pass


class LoanLimitExceededError(Exception):
    pass


class LoanAlreadyReturnedError(Exception):
    pass


class LoanNotReturnedError(Exception):
    pass


class LoanAlreadyReturnedCancelError(Exception):
    pass
