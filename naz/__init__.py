"""
`naz` is an async SMPP client.

It's name is derived from Kenyan hip hop artiste, Nazizi.

`SMPP is a protocol designed for the transfer of short message data between External Short Messaging Entities(ESMEs), Routing Entities(REs) and Short Message Service Center(SMSC).` - [Wikipedia]

naz currently only supports SMPP version 3.4.

naz has no third-party dependencies and it requires python version 3.6+

naz is in active development and it's API may change in backward incompatible ways.

https://pypi.python.org/pypi/naz



[Wikipedia]: https://en.wikipedia.org/wiki/Short_Message_Peer-to-Peer

"""
from .client import Client  # noqa: F401
from .client import SmppCommand  # noqa: F401
from .client import SmppDataCoding  # noqa: F401
from .client import CommandStatus  # noqa: F401
from .client import SmppCommandStatus  # noqa: F401

from . import q  # noqa: F401
from . import throttle  # noqa: F401
from . import sequence  # noqa: F401
from . import nazcodec  # noqa: F401
from . import correlater  # noqa: F401
from . import ratelimiter  # noqa: F401

from . import __version__  # noqa: F401
