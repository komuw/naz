import codecs


class UCS2Codec(codecs.Codec):
    """
    UCS2 is for all intents & purposes assumed to be the same as
    big endian UTF16.
    """

    def encode(self, input, errors="strict"):
        # https://github.com/google/pytype/issues/348
        return codecs.utf_16_be_encode(input, errors)  # pytype: disable=module-attr

    def decode(self, input, errors="strict"):
        return codecs.utf_16_be_decode(input, errors)  # pytype: disable=module-attr


# "ucs2": UCS2Codec()
my_encoding = "ucs2"


# def search_function(my_encoding):
#     """
#     Search functions are expected to take one argument, being the encoding name in all lower case letters, and return a CodecInfo object.
#     In case a search function cannot find a given encoding, it should return None.
#     """
#     return codecs.CodecInfo(name=my_encoding, encode=UCS2Codec.encode, decode=UCS2Codec.decode)


# lambda a : a * n

codecs.register(
    lambda my_encoding: codecs.CodecInfo(
        name=my_encoding, encode=UCS2Codec.encode, decode=UCS2Codec.decode
    )
)

codecs.getencoder(my_encoding)
