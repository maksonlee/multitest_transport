"""Common constants and objects."""
import collections

CommandResult = collections.namedtuple(
    'CommandResult', ['return_code', 'stdout', 'stderr'])
