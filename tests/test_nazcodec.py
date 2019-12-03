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

from unittest import TestCase

import naz


class TestNazCodec(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_nazcodec.TestNazCodec.test_something
    """

    def test_byte_encode_guard(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-8", errors_level="strict")
        self.assertRaises(naz.nazcodec.NazCodecException, codec.encode, b"some bytes")

    def test_string_decode_guard(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-8", errors_level="strict")
        self.assertRaises(naz.nazcodec.NazCodecException, codec.decode, "unicode")

    def test_default_encoding(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-8", errors_level="strict")
        self.assertEqual(codec.encode("a"), b"a")

    def test_default_decoding(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-8", errors_level="strict")
        self.assertEqual(codec.decode(b"a"), "a")

    def test_encode_utf8(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-8", errors_level="strict")
        self.assertEqual(codec.encode("Zoë"), b"Zo\xc3\xab")

    def test_decode_utf8(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-8", errors_level="strict")
        self.assertEqual(codec.decode(b"Zo\xc3\xab"), "Zoë")

    def test_encode_utf16be(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-16be", errors_level="strict")
        self.assertEqual(codec.encode("Zoë"), b"\x00Z\x00o\x00\xeb")

    def test_decode_utf16be(self):
        codec = naz.nazcodec.SimpleCodec(encoding="utf-16be", errors_level="strict")
        self.assertEqual(codec.decode(b"\x00Z\x00o\x00\xeb"), "Zoë")

    def test_encode_ucs2(self):
        codec = naz.nazcodec.SimpleCodec(encoding="ucs2", errors_level="strict")
        self.assertEqual(codec.encode("Zoë"), b"\x00Z\x00o\x00\xeb")

    def test_decode_ucs2(self):
        codec = naz.nazcodec.SimpleCodec(encoding="ucs2", errors_level="strict")
        self.assertEqual(codec.decode(b"\x00Z\x00o\x00\xeb"), "Zoë")

    def test_encode_gsm0338(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="strict")
        self.assertEqual(
            codec.encode("HÜLK"), "".join([chr(code) for code in [72, 94, 76, 75]]).encode()
        )

    def test_encode_gsm0338_extended(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="strict")
        self.assertEqual(
            codec.encode("foo €"),
            "".join([chr(code) for code in [102, 111, 111, 32, 27, 101]]).encode(),
        )

    def test_decode_gsm0338_extended(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="strict")
        self.assertEqual(
            codec.decode("".join([chr(code) for code in [102, 111, 111, 32, 27, 101]]).encode()),
            "foo €",
        )

    def test_encode_gsm0338_strict(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="strict")
        self.assertRaises(UnicodeEncodeError, codec.encode, "Zoë")

    def test_encode_gsm0338_ignore(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="ignore")
        self.assertEqual(codec.encode("Zoë"), b"Zo")

    def test_encode_gsm0338_replace(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="replace")
        self.assertEqual(codec.encode("Zoë"), b"Zo?")

    def test_decode_gsm0338_strict(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="strict")
        self.assertRaises(UnicodeDecodeError, codec.decode, "Zoë".encode("utf-8"))

    def test_decode_gsm0338_ignore(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="ignore")
        self.assertEqual(codec.decode("Zoë".encode("utf-8")), "Zo")

    def test_decode_gsm0338_replace(self):
        codec = naz.nazcodec.SimpleCodec(encoding="gsm0338", errors_level="replace")
        self.assertEqual(codec.decode("Zoë".encode("utf-8")), "Zo??")
