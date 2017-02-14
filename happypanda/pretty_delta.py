"""Module for datetime pretty delta."""
import datetime


class PrettyDelta:
    """Pretty delta datetime.

    Attributes:
        day (int): day of delta
        second (int): second of delta
        year (int): year of delta
        month (int): month of delta
        hour (int): hour of delta
        minute (int): minute of delta
    """

    def __init__(self, dt):
        """init method."""
        now = datetime.datetime.now()

        delta = now - dt
        self.day = delta.days
        self.second = delta.seconds

        self.year, self.day = self.q_n_r(self.day, 365)
        self.month, self.day = self.q_n_r(self.day, 30)
        self.hour, self.second = self.q_n_r(self.second, 3600)
        self.minute, self.second = self.q_n_r(self.second, 60)

    @staticmethod
    def q_n_r(a, b):
        """Return quotient and remaining.

        Args:
            a: Divident.
            b: Divisor.

        Returns:
            Tuple of (quotient, remaining)
        """
        return a / b, a % b

    def format(self):
        """Pretty delta Format.

        Returns:
            str: readable pretty delta datetime.
        """
        for period in ['year', 'month', 'day', 'hour', 'minute', 'second']:
            n = getattr(self, period)
            if n > 0.9:
                return self.formatn(n, period)
        return "0 second"

    @staticmethod
    def formatn(n, s):
        """Add "s" if it's plural.

        Args:
            n: Amount of subject.
            s: Subject
        """
        if n == 1:
            return "1 {}".format(s)
        elif n > 1:
            return "{} {}s".format(n, s)
