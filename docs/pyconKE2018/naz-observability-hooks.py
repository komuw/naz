import sqlite3
import naz

class SetMessageStateHook(naz.hooks.BaseHook):
    async def request(self, smpp_event, correlation_id):
        pass
    async def response(self, smpp_event, correlation_id):
        if smpp_event == "deliver_sm":
            conn = sqlite3.connect('mySmsDB.db')
            c = conn.cursor()
            t = (correlation_id,)
            c.execute("UPDATE \
                       SmsTable \
                       SET State='delivered' \
                       WHERE CorrelatinID=?", t)
            conn.commit()
            conn.close()

stateHook = SetMessageStateHook()
cli = naz.Client(
    ...
    hook=stateHook,
)

import naz
from prometheus_client import Counter

class MyPrometheusHook(naz.hooks.BaseHook):
    async def request(self, smpp_event, correlation_id):
        c = Counter('my_requests', 'Description of counter')
        c.inc() # Increment by 1
    async def response(self, smpp_event, correlation_id):
        c = Counter('my_responses', 'Description of counter')
        c.inc() # Increment by 1

myHook = MyPrometheusHook()
cli = naz.Client(
    ...
    hook=myHook,
)