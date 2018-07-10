class BaseSequenceGenerator:
    """
    Interface that must be implemented to satisfy naz's sequence generator.
    User implementations should inherit this class and
    implement the next_sequence method with the type signatures shown.

    sequence_number is an Integer of size 4 octets, which allows SMPP requests and responses to be correlated.
    The sequence_number should increase monotonically.
    And they ought to be in the range 0x00000001 to 0x7FFFFFFF
    see section 3.2 of smpp ver 3.4 spec document.

    You can supply your own sequence generator, so long as it respects the range defined in the SMPP spec.
    """

    def next_sequence(self) -> int:
        """
        method that returns a monotonically increasing Integer in the range 0x00000001 to 0x7FFFFFFF
        """
        raise NotImplementedError("next_sequence method must be implemented.")


class SimpleSequenceGenerator(BaseSequenceGenerator):
    """
    implement's naz BaseSequenceGenerator interface
    """

    min_sequence_number: int = 0x00000001
    max_sequence_number: int = 0x7FFFFFFF

    def __init__(self) -> None:
        self.sequence_number: int = self.min_sequence_number

    def next_sequence(self) -> int:
        if self.sequence_number == self.max_sequence_number:
            # wrap around
            self.sequence_number = self.min_sequence_number
        else:
            self.sequence_number += 1
        return self.sequence_number
