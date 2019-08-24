import os
import sys
import logging
import importlib

import naz


def load_class(dotted_path: str, logger: naz.log.BaseLogger) -> naz.Client:
    """
    taken from: https://github.com/coleifer/huey/blob/4138d454cc6fd4d252c9350dbd88d74dd3c67dcb/huey/utils.py#L44
    huey is released under MIT license a copy of which can be found at: https://github.com/coleifer/huey/blob/master/LICENSE

    The license is also included below:

    Copyright (c) 2017 Charles Leifer

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
    """
    try:
        path, klass = dotted_path.rsplit(".", 1)
        mod = importlib.import_module(path)
        attttr = getattr(mod, klass)
        return attttr
    except Exception as e:
        cur_dir = os.getcwd()
        if cur_dir not in sys.path:
            sys.path.insert(0, cur_dir)
            return load_class(dotted_path, logger)
        err_message = "Error importing {0}".format(dotted_path)
        logger.log(
            logging.ERROR,
            {"event": "naz.cli.main", "stage": "end", "state": err_message, "error": str(e)},
        )
        raise e
