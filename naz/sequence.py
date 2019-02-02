import abc


class BaseSequenceGenerator(abc.ABC):
    """
    Interface that must be implemented to satisfy naz's sequence generator.
    User implementations should inherit this class and
    implement the :func:`next_sequence <BaseSequenceGenerator.next_sequence>` methods with the type signatures shown.

    In SMPP, sequence_number is an Integer which allows SMPP requests and responses to be correlated.
    The sequence_number should increase monotonically and ought to be in the range 1 - 2,147,483,647

    The sequence_number should wrap around when it reaches the maximum allowed by SMPP specification.
    """

    @abc.abstractmethod
    def next_sequence(self) -> int:
        """
        method that returns a monotonically increasing Integer in the range 1 - 2,147,483,647
        """
        raise NotImplementedError("next_sequence method must be implemented.")


class SimpleSequenceGenerator(BaseSequenceGenerator):
    """
    This is an implementation of BaseSequenceGenerator.
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
