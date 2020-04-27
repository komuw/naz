# The code in this file is copied from https://github.com/praekelt/vumi/blob/master/vumi/codecs/vumi_codecs.py
# which is in turn largely copied from http://stackoverflow.com/questions/13130935/decode-7-bit-gsm
# Vumi's license is included below:

# Copyright (c) Praekelt Foundation and individual contributors.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#     1.  Redistributions of source code must retain the above copyright notice,
#         this list of conditions and the following disclaimer.

#     2.  Redistributions in binary form must reproduce the above copyright
#         notice, this list of conditions and the following disclaimer in the
#         documentation and/or other materials provided with the distribution.

#     3.  Neither the name of the Praekelt Foundation nor the names of its
#         contributors may be used to endorse or promote products derived from
#         this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import codecs
import typing


# An alternative to using this codec module is to use: https://github.com/dsch/gsm0338
# however, I'm guessing that vumi has been in use longer and we should thus go with it.


class NazCodecException(Exception):
    pass


class GSM7BitCodec(codecs.Codec):
    """
    SMPP uses a 7-bit GSM character set.
    This class implements that encoding/decoding scheme.
    Users should never have to use this directly, instead; use `naz.protocol.SubmitSM(encoding="gsm0338")`

    Example Usage:

    .. highlight:: python
    .. code-block:: python

        import naz

        codec = naz.codec.GSM7BitCodec()
        codec.encode("foo €")
    """

    gsm_basic_charset = (
        "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;"
        "<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäö"
        "ñüà"
    )

    gsm_basic_charset_map = dict((l, i) for i, l in enumerate(gsm_basic_charset))

    gsm_extension = (
        "````````````````````^```````````````````{}`````\\````````````[~]`"
        "|````````````````````````````````````€``````````````````````````"
    )

    gsm_extension_map = dict((l, i) for i, l in enumerate(gsm_extension))

    def encode(self, input, errors="strict"):
        """
        return an encoded version of the string as a bytes object.

        Parameters:
            input: the string to encode
            errors:	same meaning as the errors argument to pythons' `encode <https://docs.python.org/3/library/codecs.html#codecs.encode>`_ method
        """
        result = []
        for position, c in enumerate(input):
            idx = self.gsm_basic_charset_map.get(c)
            if idx is not None:
                result.append(chr(idx))
                continue
            idx = self.gsm_extension_map.get(c)
            if idx is not None:
                result.append(chr(27) + chr(idx))
            else:
                result.append(self._handle_encode_error(c, errors, position, input))

        obj = "".join(result)
        # this is equivalent to;
        # import six; six.b('someString')
        # see:
        # https://github.com/benjaminp/six/blob/68112f3193c7d4bef5ad86ed1b6ed528edd9093d/six.py#L625
        obj = obj.encode("latin-1")
        return (obj, len(obj))

    def decode(self, input, errors="strict"):
        """
        return a string decoded from the given bytes.

        Parameters:
            input: the bytes to decode
            errors:	same meaning as the errors argument to pythons' `encode <https://docs.python.org/3/library/codecs.html#codecs.encode>`_ method
        """
        res = iter(input)
        result = []
        for position, c in enumerate(res):
            try:
                if c == 27:
                    c = next(res)
                    result.append(self.gsm_extension[c])
                else:
                    result.append(self.gsm_basic_charset[c])
            except IndexError as indexErrorException:
                result.append(
                    self._handle_decode_error(c, errors, position, input, indexErrorException)
                )

        obj = "".join(result)
        return (obj, len(obj))

    def _handle_encode_error(self, char, handler_type, position, obj):
        handler = getattr(self, "handle_encode_%s_error" % (handler_type,), None)
        if handler is None:
            raise NazCodecException("Invalid errors type %s for GSM7BitCodec", handler_type)
        return handler(char, position, obj)

    @staticmethod
    def _handle_encode_strict_error(char, position, obj):
        raise UnicodeEncodeError("gsm0338", char, position, position + 1, repr(obj))

    @staticmethod
    def _handle_encode_ignore_error(char, position, obj):
        return ""

    def _handle_encode_replace_error(self, char, position, obj):
        return chr(self.gsm_basic_charset_map.get("?"))

    def _handle_decode_error(self, char, handler_type, position, obj, indexErrorException):
        handler = getattr(self, "handle_decode_%s_error" % (handler_type,), None)
        if handler is None:
            raise NazCodecException("Invalid errors type %s for GSM7BitCodec", handler_type)
        return handler(char, position, obj, indexErrorException)

    @staticmethod
    def _handle_decode_strict_error(char, position, obj, indexErrorException):
        # https://github.com/google/pytype/issues/349
        raise UnicodeDecodeError(
            "gsm0338",
            chr(char).encode("latin-1"),
            position,
            position + 1,
            repr(obj),  # pytype: disable=wrong-arg-types
        ) from indexErrorException

    @staticmethod
    def _handle_decode_ignore_error(char, position, obj, indexErrorException):
        return ""

    @staticmethod
    def _handle_decode_replace_error(char, position, obj, indexErrorException):
        return "?"


class UCS2Codec(codecs.Codec):
    """
    This class implements the UCS2 encoding/decoding scheme.
    Users should never have to use this directly, instead; use `naz.protocol.SubmitSM(encoding="ucs2")`

    UCS2 is for all intents & purposes assumed to be the same as big endian UTF16.
    """

    def encode(self, input, errors="strict"):
        """
        return an encoded version of the string as a bytes object.

        Parameters:
            input: the string to encode
            errors:	same meaning as the errors argument to pythons' `encode <https://docs.python.org/3/library/codecs.html#codecs.encode>`_ method
        """
        # https://github.com/google/pytype/issues/348
        return codecs.utf_16_be_encode(input, errors)  # pytype: disable=module-attr

    def decode(self, input, errors="strict"):
        """
        return a string decoded from the given bytes.

        Parameters:
            input: the bytes to decode
            errors:	same meaning as the errors argument to pythons' `encode <https://docs.python.org/3/library/codecs.html#codecs.encode>`_ method
        """
        return codecs.utf_16_be_decode(input, errors)  # pytype: disable=module-attr


_INBUILT_CODECS: typing.Dict[str, codecs.CodecInfo] = {
    "ucs2": codecs.CodecInfo(name="ucs2", encode=UCS2Codec.encode, decode=UCS2Codec.decode),
    "gsm0338": codecs.CodecInfo(
        name="gsm0338", encode=GSM7BitCodec.encode, decode=GSM7BitCodec.decode
    ),
}


def register_codecs(custom_codecs: typing.Union[None, typing.Dict[str, codecs.CodecInfo]] = None):
    """
    Register codecs, both custom and naz inbuilt ones.
    Custom codecs that have same encoding as inbuilt ones will take precedence.

    Parameters:
        custom_codecs: a list of custom codecs to register.
    """
    if custom_codecs is None:
        custom_codecs = {}

    # Note: Search function registration is not currently reversible,
    # which may cause problems in some cases, such as unit testing or module reloading.
    # https://docs.python.org/3.7/library/codecs.html#codecs.register

    def _codec_search_function(_encoding):
        """
        We should try and get codecs from the custom_codecs first.
        This way, if someone had overridden an inbuilt codec, their
        implementation is chosen first and cached.
        """
        return custom_codecs.get(_encoding, _INBUILT_CODECS.get(_encoding))

    codecs.register(_codec_search_function)
