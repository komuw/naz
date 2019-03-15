## naz changelog:
most recent version is listed first.


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
