Welcome to naz's documentation!
===============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


## cool
```python
import naz
from prometheus_client import Counter

class MyPrometheusHook(naz.hooks.BaseHook):
    async def request(self, smpp_command, log_id, hook_metadata):
        c = Counter('my_requests', 'Description of counter')
        c.inc() # Increment by 1
    async def response(self,
                       smpp_command,
                       log_id,
                       hook_metadata,
                       smsc_response):
        c = Counter('my_responses', 'Description of counter')
        c.inc() # Increment by 1

myHook = MyPrometheusHook()
cli = naz.Client(
    ...
    hook=myHook,
)
```


## Markdown Header

Foo in **Markdown**, which means we can do **inline *italics* like this**

#### Markdown Lower Header

More second-level content.

[A link](http://rtfd.org)

You can even do:

```bash

echo "Hello"
```
