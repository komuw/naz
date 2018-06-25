import codecs
import sys

class VumiCodecException(Exception):
    pass

class GSM7BitCodec(codecs.Codec):
    """
    This has largely been copied from:
    http://stackoverflow.com/questions/13130935/decode-7-bit-gsm
    """

    gsm_basic_charset = (
        "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;"
        "<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäö"
        "ñüà")

    gsm_basic_charset_map = dict(
        (l, i) for i, l in enumerate(gsm_basic_charset))

    gsm_extension = (
        "````````````````````^```````````````````{}`````\\````````````[~]`"
        "|````````````````````````````````````€``````````````````````````")

    gsm_extension_map = dict((l, i) for i, l in enumerate(gsm_extension))

    def encode(self, unicode_string, errors='strict'):
        """
        errors can be 'strict', 'replace' or 'ignore'
        eg:
            xcodec.encode("Zoë","gsm0338") will fail with UnicodeEncodeError
            but
            xcodec.encode("Zoë","gsm0338", 'replace') will return b'Zo?'
            and
            xcodec.encode("Zoë","gsm0338", 'ignore') will return b'Zo'
        """
        result = []
        for position, c in enumerate(unicode_string):
            idx = self.gsm_basic_charset_map.get(c)
            if idx is not None:
                result.append(chr(idx))
                continue
            idx = self.gsm_extension_map.get(c)
            if idx is not None:
                result.append(chr(27) + chr(idx))
            else:
                result.append(
                    self.handle_encode_error( c, errors, position, unicode_string))

        obj = ''.join(result)
        # this is equivalent to;
        # import six; six.b('someString')
        # see: https://github.com/benjaminp/six/blob/68112f3193c7d4bef5ad86ed1b6ed528edd9093d/six.py#L625
        obj = obj.encode("latin-1")
        return (obj, len(obj))

    def handle_encode_error(self, char, handler_type, position, obj):
        handler = getattr(
            self, 'handle_encode_%s_error' % (handler_type,), None)
        if handler is None:
            raise VumiCodecException(
                'Invalid errors type %s for GSM7BitCodec', handler_type)
        return handler(char, position, obj)

    def handle_encode_strict_error(self, char, position, obj):
        raise UnicodeEncodeError('gsm0338', char, position, position + 1, repr(obj))

    def handle_encode_ignore_error(self, char, position, obj):
        return ''

    def handle_encode_replace_error(self, char, position, obj):
        return chr(self.gsm_basic_charset_map.get('?'))

    def decode(self, byte_string, errors='strict'):
        """
        errors can be 'strict', 'replace' or 'ignore'
        """
        res = iter(byte_string)
        result = []
        for position, c in enumerate(res):
            try:
                if c == 27:
                    c = next(res)
                    result.append(self.gsm_extension[c])
                else:
                    result.append(self.gsm_basic_charset[c])
            except IndexError:
                result.append(self.handle_decode_error(c, errors, position, byte_string))

        obj = ''.join(result)
        return (obj, len(obj))

    def handle_decode_error(self, char, handler_type, position, obj):
        handler = getattr(
            self, 'handle_decode_%s_error' % (handler_type,), None)
        if handler is None:
            raise VumiCodecException(
                'Invalid errors type %s for GSM7BitCodec', handler_type)
        return handler(char, position, obj)

    def handle_decode_strict_error(self, char, position, obj):
        raise UnicodeDecodeError('gsm0338', chr(char).encode('latin-1'), position, position + 1, repr(obj))
                           

    def handle_decode_ignore_error(self, char, position, obj):
        return ''

    def handle_decode_replace_error(self, char, position, obj):
        return '?'


class UCS2Codec(codecs.Codec):
    """
    UCS2 is for all intents & purposes assumed to be the same as
    big endian UTF16.
    """
    def encode(self, input, errors='strict'):
        return codecs.utf_16_be_encode(input, errors)

    def decode(self, input, errors='strict'):
        return codecs.utf_16_be_decode(input, errors)


class VumiCodec(object):
    custom_codecs = {
        'gsm0338': GSM7BitCodec(),
        'ucs2': UCS2Codec()
    }

    def encode(self, unicode_string, encoding=None, errors='strict'):
        """
        you should call encode on a string. ie in python3 we write;
          'sss'.encode() # b'sss'
        """
        if not isinstance(unicode_string, str):
            raise VumiCodecException(
                'Only Unicode strings accepted for encoding.')
        encoding = encoding or sys.getdefaultencoding()
        if encoding in self.custom_codecs:
            encoder = self.custom_codecs[encoding].encode
        else:
            encoder = codecs.getencoder(encoding)
        obj, length = encoder(unicode_string, errors)
        return obj

    def decode(self, byte_string, encoding=None, errors='strict'):
        """
        you should call decode on a byte. ie in python3 we write;
          b'sss'.decode() # 'sss'
        """
        # if not isinstance(byte_string, str):
        #     raise VumiCodecException(
        #         'Only bytestrings accepted for decoding.')
        if not isinstance(byte_string, (bytes, bytearray)):
            raise VumiCodecException('Only bytestrings accepted for decoding.')
        encoding = encoding or sys.getdefaultencoding()
        if encoding in self.custom_codecs:
            decoder = self.custom_codecs[encoding].decode
        else:
            decoder = codecs.getdecoder(encoding)
        obj, length = decoder(byte_string, errors)
        return obj

xcodec = VumiCodec()
xcodec.encode('Привет мир!\n', "gsm0338")
# import pdb;pdb.set_trace()
# xcodec.decode('Zo\xc3\xab', 'gsm0338')
# import pdb;pdb.set_trace()
# xcodec.encode("Zoë", "utf-16be")
# xcodec.encode("HÜLK", "gsm0338")
#  xcodec.encode('Привет мир!\n', "gsm0338") 
# xcodec.decode('Zo\xc3\xab', 'gsm0338')
print("cool")
print("cool")
print("cool")
print("cool")
print("cool")