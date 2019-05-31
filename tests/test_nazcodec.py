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

    def setUp(self):
        self.codec = naz.nazcodec.SimpleNazCodec()

    def test_byte_encode_guard(self):
        self.assertRaises(
            naz.nazcodec.NazCodecException, self.codec.encode, b"some bytes", "utf-8", "strict"
        )

    def test_string_decode_guard(self):
        self.assertRaises(
            naz.nazcodec.NazCodecException, self.codec.decode, "unicode", "utf-8", "strict"
        )

    def test_default_encoding(self):
        self.assertEqual(self.codec.encode("a", "utf-8", "strict"), b"a")

    def test_default_decoding(self):
        self.assertEqual(self.codec.decode(b"a", "utf-8", "strict"), "a")

    def test_encode_utf8(self):
        self.assertEqual(self.codec.encode("Zoë", "utf-8", "strict"), b"Zo\xc3\xab")

    def test_decode_utf8(self):
        self.assertEqual(self.codec.decode(b"Zo\xc3\xab", "utf-8", "strict"), "Zoë")

    def test_encode_utf16be(self):
        self.assertEqual(self.codec.encode("Zoë", "utf-16be", "strict"), b"\x00Z\x00o\x00\xeb")

    def test_decode_utf16be(self):
        self.assertEqual(self.codec.decode(b"\x00Z\x00o\x00\xeb", "utf-16be", "strict"), "Zoë")

    def test_encode_ucs2(self):
        self.assertEqual(self.codec.encode("Zoë", "ucs2", "strict"), b"\x00Z\x00o\x00\xeb")

    def test_decode_ucs2(self):
        self.assertEqual(self.codec.decode(b"\x00Z\x00o\x00\xeb", "ucs2", "strict"), "Zoë")

    def test_encode_gsm0338(self):
        self.assertEqual(
            self.codec.encode("HÜLK", "gsm0338", "strict"),
            "".join([chr(code) for code in [72, 94, 76, 75]]).encode(),
        )

    def test_encode_gsm0338_extended(self):
        self.assertEqual(
            self.codec.encode("foo €", "gsm0338", "strict"),
            "".join([chr(code) for code in [102, 111, 111, 32, 27, 101]]).encode(),
        )

    def test_decode_gsm0338_extended(self):
        self.assertEqual(
            self.codec.decode(
                "".join([chr(code) for code in [102, 111, 111, 32, 27, 101]]).encode(),
                "gsm0338",
                "strict",
            ),
            "foo €",
        )

    def test_encode_gsm0338_strict(self):
        self.assertRaises(UnicodeEncodeError, self.codec.encode, "Zoë", "gsm0338", "strict")

    def test_encode_gsm0338_ignore(self):
        self.assertEqual(self.codec.encode("Zoë", "gsm0338", "ignore"), b"Zo")

    def test_encode_gsm0338_replace(self):
        self.assertEqual(self.codec.encode("Zoë", "gsm0338", "replace"), b"Zo?")

    def test_decode_gsm0338_strict(self):
        self.assertRaises(
            UnicodeDecodeError, self.codec.decode, "Zoë".encode("utf-8"), "gsm0338", "strict"
        )

    def test_decode_gsm0338_ignore(self):
        self.assertEqual(self.codec.decode("Zoë".encode("utf-8"), "gsm0338", "ignore"), "Zo")

    def test_decode_gsm0338_replace(self):
        self.assertEqual(self.codec.decode("Zoë".encode("utf-8"), "gsm0338", "replace"), "Zo??")
