from ..errors import ZenodoRDMError


class ConfirmationEmailNotSent(ZenodoRDMError):
    def __init__(self, message):
        """Initialise error."""
        super().__init__(
                "Confirmation email failed to send. Error: {}".format(message)
        )

class SupportEmailNotSent(ZenodoRDMError):
    def __init__(self, message):
        """Initialise error."""
        super().__init__(
                "Support email failed to send. Error: {}".format(message)
        )


class FormValidationError(ZenodoRDMError):
    pass