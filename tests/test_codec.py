# The code in this file is copied from https://github.com/praekelt/vumi/blob/master/vumi/codecs/tests/test_vumi_codecs.py
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
from unittest import TestCase

import naz


class TestCodec(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_codec.TestCodec.test_something
    """

    def test_byte_encode_guard(self):
        codec = codecs.lookup("utf-8")
        self.assertRaises(TypeError, codec.encode, b"some bytes")

    def test_string_decode_guard(self):
        codec = codecs.lookup("utf-8")
        self.assertRaises(TypeError, codec.decode, "unicode")

    def test_default_encoding(self):
        codec = codecs.lookup("utf-8")
        self.assertEqual(codec.encode("a")[0], b"a")

    def test_default_decoding(self):
        codec = codecs.lookup("utf-8")
        self.assertEqual(codec.decode(b"a")[0], "a")

    def test_encode_utf8(self):
        codec = codecs.lookup("utf-8")
        self.assertEqual(codec.encode("Zoë")[0], b"Zo\xc3\xab")

    def test_decode_utf8(self):
        codec = codecs.lookup("utf-8")
        self.assertEqual(codec.decode(b"Zo\xc3\xab")[0], "Zoë")

    def test_encode_utf16be(self):
        codec = codecs.lookup("utf-16be")
        self.assertEqual(codec.encode("Zoë")[0], b"\x00Z\x00o\x00\xeb")

    def test_decode_utf16be(self):
        codec = codecs.lookup("utf-16be")
        self.assertEqual(codec.decode(b"\x00Z\x00o\x00\xeb")[0], "Zoë")

    def test_encode_ucs2(self):
        codec = naz.codec.UCS2Codec()
        self.assertEqual(codec.encode("Zoë")[0], b"\x00Z\x00o\x00\xeb")

    def test_decode_ucs2(self):
        codec = naz.codec.UCS2Codec()
        self.assertEqual(codec.decode(b"\x00Z\x00o\x00\xeb")[0], "Zoë")

    def test_encode_gsm0338(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertEqual(
            codec.encode("HÜLK")[0], "".join([chr(code) for code in [72, 94, 76, 75]]).encode()
        )

    def test_encode_gsm0338_extended(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertEqual(
            codec.encode("foo €")[0],
            "".join([chr(code) for code in [102, 111, 111, 32, 27, 101]]).encode(),
        )

    def test_decode_gsm0338_extended(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertEqual(
            codec.decode("".join([chr(code) for code in [102, 111, 111, 32, 27, 101]]).encode())[0],
            "foo €",
        )

    def test_encode_gsm0338_strict(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertRaises(UnicodeEncodeError, codec.encode, "Zoë", "strict")

    def test_encode_gsm0338_ignore(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertEqual(codec.encode("Zoë", "ignore")[0], b"Zo")

    def test_encode_gsm0338_replace(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertEqual(codec.encode("Zoë", "replace")[0], b"Zo?")

    def test_decode_gsm0338_strict(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertRaises(UnicodeDecodeError, codec.decode, "Zoë".encode("utf-8"), "strict")

    def test_decode_gsm0338_ignore(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertEqual(codec.decode("Zoë".encode("utf-8"), "ignore")[0], "Zo")

    def test_decode_gsm0338_replace(self):
        codec = naz.codec.GSM7BitCodec()
        self.assertEqual(codec.decode("Zoë".encode("utf-8"), "replace")[0], "Zo??")


class TestCodecRegistration(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_codec.TestCodecRegistration.test_something
    """

    def test_registration_of_inbuilt_codecs(self):
        # register
        naz.codec.register_codecs()

        for k, _ in naz.codec._INBUILT_CODECS.items():
            codec = codecs.lookup(k)
            self.assertEqual(codec.name, k)

    def test_registration_of_custom_codecs(self):
        _sheng_encoding = "kenyan_sheng"
        with self.assertRaises(LookupError):
            codecs.lookup(_sheng_encoding)

        class KenyanShengCodec(codecs.Codec):
            # All the methods have to be staticmethods because they are passed to `codecs.CodecInfo`
            @staticmethod
            def encode(input, errors="strict"):
                return codecs.utf_8_encode(input, errors)

            @staticmethod
            def decode(input, errors="strict"):
                return codecs.utf_8_decode(input, errors)

        custom_codecs = {
            _sheng_encoding: codecs.CodecInfo(
                name=_sheng_encoding,
                encode=KenyanShengCodec.encode,
                decode=KenyanShengCodec.decode,
            ),
        }

        # register
        naz.codec.register_codecs(custom_codecs)

        codec = codecs.lookup(_sheng_encoding)
        self.assertEqual(codec.name, _sheng_encoding)

    def test_codec_overriding(self):
        """
        tests that users can be able to override an inbuilt codec
        with their own implementation.
        """

        class OverridingCodec(codecs.Codec):
            # All the methods have to be staticmethods because they are passed to `codecs.CodecInfo`
            @staticmethod
            def encode(input, errors="strict"):
                return codecs.utf_8_encode(input, errors)

            @staticmethod
            def decode(input, errors="strict"):
                return codecs.utf_8_decode(input, errors)

        custom_codecs = {
            "gsm0338": codecs.CodecInfo(
                name="gsm0338", encode=OverridingCodec.encode, decode=OverridingCodec.decode,
            ),
        }

        # register, this will override inbuilt `gsm0338` codec with a custom one.
        naz.codec.register_codecs(custom_codecs)

        new_codec = codecs.lookup("gsm0338")
        self.assertNotEqual(new_codec.encode, naz.codec.GSM7BitCodec.encode)
        self.assertNotEqual(new_codec.decode, naz.codec.GSM7BitCodec.decode)
        self.assertEqual(new_codec.encode, OverridingCodec.encode)
