## `naz` changelog:
most recent version is listed first.


## **version:** v0.8.1
- Fix a previously skipped test: https://github.com/komuw/naz/pull/209  
- Reconnect after `unbind_and_disconnect` in `recieve_data` lifecycle: https://github.com/komuw/naz/pull/212

## **version:** v0.8.0
- Bugfix - RuntimeError: Cannot call `write()` after `write_eof()`: https://github.com/komuw/naz/pull/208   
- support Smpp Optional Tags in `submit_sm`: https://github.com/komuw/naz/pull/202, https://github.com/komuw/naz/pull/207  
- Fixed some flaky tests: https://github.com/komuw/naz/pull/204, https://github.com/komuw/naz/pull/206  
- Add ability to use different codecs for different messages while using the same `naz` client: https://github.com/komuw/naz/pull/201   
  With this change, message encoding is now a property of the message and not the client.


## **version:** v0.7.9
- During shutdown, only close the writer without closing the reader end of the transport: https://github.com/komuw/naz/pull/198


## **version:** v0.7.8
- Rename `naz.Client.rateLimiter` to `naz.Client.rate_limiter`: https://github.com/komuw/naz/pull/195      
  This was done so as to maintain consistency with other `naz.Client` attributes.    
- Fix a bug where `naz` was not formatting 1octet integers correctly : https://github.com/komuw/naz/pull/196


## **version:** v0.7.7
- support python version 3.8: https://github.com/komuw/naz/pull/186   


## **version:** v0.7.6
- Add ability to supply more `submit_sm` parameters when enquiuing `submit_sm`: https://github.com/komuw/naz/pull/193


## **version:** v0.7.5
- Rename `naz.nazcodec.BaseNazCodec` to `naz.codec.BaseCodec`: https://github.com/komuw/naz/pull/191  
- Rename `naz.Client.codec_class` to `naz.Client.codec`: https://github.com/komuw/naz/pull/191  
- Add ability for `naz.log.SimpleLogger` to render logs as a python dictionary: https://github.com/komuw/naz/pull/191  
- BugFix, `data_coding` should not be applied to all fields that are of type C-octet string: https://github.com/komuw/naz/pull/190     
- Have the naz messsage protocol only use utf8 for encoding/decoding: https://github.com/komuw/naz/pull/190    


## **version:** v0.7.4
- Fix a bug that prevented `enquire_link` and `deliver_sm` from been sent: https://github.com/komuw/naz/pull/179  
- Enforce `naz` message protocol in code: https://github.com/komuw/naz/pull/179
- make `naz.Client.logger` to be a python `logging.Handler`: https://github.com/komuw/naz/pull/181
- carry out fuzzy testing: https://github.com/komuw/naz/pull/178
- re-run benchmarks: https://github.com/komuw/naz/pull/182


## **version:** v0.7.3
- make `naz.SimpleCorrelater.delete_after_ttl()` private: https://github.com/komuw/naz/pull/172
- rename `naz.broker.BaseOutboundQueue` to `naz.broker.BaseBroker`: https://github.com/komuw/naz/pull/174     
  this is the more idiomatic name for what it is.     
- re-run benchmarks after renmaing Queue to Broker: https://github.com/komuw/naz/pull/176


## **version:** v0.7.2  
- fix infinite loop bug, which could occur while re-establishing connection & re-binding to SMSC: https://github.com/komuw/naz/pull/171


## **version:** v0.7.1 
- add ability to start `naz` even when SMSC is down: https://github.com/komuw/naz/pull/168    
  this may be important when you want to deploy `naz` when the mno/SMSC is down and you want `naz` to automatically connect when the SMSC comes back online.


## **version:** v0.7.0
- Use python 3.7 since it has better `async/await` support: https://github.com/komuw/naz/pull/166


## **version:** v0.6.8
- add target level to Breachandler: https://github.com/komuw/naz/pull/163


## **version:** v0.6.7
- make available to `hooks` the raw pdu as sent/received to/from SMSC: https://github.com/komuw/naz/pull/159
- rename the `naz.hooks.BaseHook` methods: https://github.com/komuw/naz/pull/159 
  The new names are more correct and indicate what is actually taking place.
- use github actions for CI: https://github.com/komuw/naz/pull/162
- Add heartbeat to BreachHandler: https://github.com/komuw/naz/pull/161


## **version:** v0.6.6
- make sure that `naz` reads exactly the first 4bytes of an smpp header: https://github.com/komuw/naz/pull/153  
  - if `naz` is unable to read exactly those bytes, it unbinds and closes the connection
  - this is so as to ensure that `naz` behaves correctly and does not enter into an inconsistent state.
- make sire that `naz` reads exacly the first 16bytes of the smpp header: https://github.com/komuw/naz/pull/155   
  - this builds on the [earlier work](https://github.com/komuw/naz/pull/153) but now `naz` takes it a step further and will unbind & close connection if it is unable to read the entire SMPP header
  - this is done to prevent inconsistency and also to try and be faithful to the smpp spec.
- enhance type annotations of `naz.log`: https://github.com/komuw/naz/pull/156


## **version:** v0.6.5
- Simplify Breach log handler: https://github.com/komuw/naz/pull/152


## **version:** v0.6.4
- added a logging BreachHandler: https://github.com/komuw/naz/pull/149
- renamed `naz.logger` to `naz.log`: https://github.com/komuw/naz/pull/150
- fix documentation styling: https://github.com/komuw/naz/pull/151


## **version:** v0.6.3
- added static analysis support using pytype: https://github.com/komuw/naz/pull/148


## **version:** v0.6.2
- If `naz` were to encounter an SMPP protocol error, it now bails early by unbinding and closing connection: https://github.com/komuw/naz/pull/147


## **version:** v0.6.1
- all the changes in `v0.6.0-beta.1`
- fix a number of logging issues: https://github.com/komuw/naz/pull/105
- cleanly handle termination signals like `SIGTERM`: https://github.com/komuw/naz/pull/106
- validate `naz.Client` arguments: https://github.com/komuw/naz/pull/108
- remove ability to bring your own eventloop: https://github.com/komuw/naz/pull/111
- make `naz` more fault tolerant: https://github.com/komuw/naz/pull/113
  - `naz` now has a configurable timeout when trying to connect to SMSC
  - `naz` will now be able to detect when the connection to SMSC is disconnected and will attempt to re-connect & re-bind
  - bugfix; `asyncio.streams.StreamWriter.drain` should not be called concurrently by multiple coroutines
  - when shutting down, `naz` now tries to make sure that write buffers are properly flushed.
- replace naz json config file with a python file: https://github.com/komuw/naz/pull/123
- bugfix: `naz` would attempt to send messages(`submit_sm`) out before it had even connected to SMSC: https://github.com/komuw/naz/pull/124    
- added `naz` benchmarks and related fixes that came from the benchmark runs: https://github.com/komuw/naz/pull/127
  - when smsc returns `ESME_RMSGQFUL`(message queue is full), `naz` will now call the `throttling` handler.  
  - fixed a potential memory leak bug in `naz.correlater.SimpleCorrelater`
  - added a configurable `connection_timeout` which is the duration that `naz` will wait, for connection related activities with SMSC, before timing out.
  - `naz` is now able to re-establish connection and re-bind if the connection between it and SMSC is disconnected.  
- renamed `connection_timeout` to `socket_timeout`: https://github.com/komuw/naz/pull/141
- added benchmarks results: https://github.com/komuw/naz/pull/141
- updated documentation and moved it to [komuw.github.io/naz](https://komuw.github.io/naz/); https://github.com/komuw/naz/pull/146


## **version:** v0.6.0-beta.1
- Bug fix: https://github.com/komuw/naz/pull/98    
    the way `naz` was handling correlations was:
    - when sending `submit_sm` we save the `sequence_number`
    - when we get `submit_sm_resp` we use its `sequence_number` and look it up from Correlater  
    - when we get a `deliver_sm` request, we use its `sequence_number` and look it up from Correlater

    The way `naz` now does it after the fix is;
    - when sending `submit_sm` we save the sequence_number
    - when we get `submit_sm_resp` we lookup sequence_number and use it for correlation
    - Additionally, `submit_sm_resp` has a `message_id` in the body. This is the SMSC message ID of the submitted message.
    - We take this `message_id` and save it.
    - when we get a `deliver_sm` request, it includes a `receipted_message_id` in the optional body parameters.
    - we get that `receipted_message_id` and use it to lookup from where we had saved the one from `submit_sm_resp`
- This release also features an enhancement(and better tests) of correlation: https://github.com/komuw/naz/pull/98  


## **version:** v0.5.0-beta.1
- Add sphinx documentation: https://github.com/komuw/naz/pull/92
- Start tracking changes in a changelog
- Add more type hints and also run `mypy` across the entire repo: https://github.com/komuw/naz/pull/92
- It's now possible to bring your own logger: https://github.com/komuw/naz/pull/93
- Made the various interfaces in `naz` to inherit from `abc.ABC`: https://github.com/komuw/naz/pull/95
- Fixed a few stylistic issues raised by codacy: https://github.com/komuw/naz/pull/96
