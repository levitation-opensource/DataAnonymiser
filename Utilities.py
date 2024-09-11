# -*- coding: utf-8 -*-

#
# Author: Roland Pihlakas, 2021 - 2024
#
# roland@simplify.ee
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#


import os
import sys

import io
import gzip
import pickle
import json_tricks
# import re
import regex

import time
# import textwrap
import shutil
import traceback

# import re
import codecs
import hashlib
import base64

# from progressbar import ProgressBar # NB! need to load it before init_logging is called else progress bars do not work properly for some reason

# import requests
import asyncio
# import aiohttp
import aiofiles                       # supports flush method
import aiofiles.os

import functools
# from functools import reduce
# import operator

from collections import OrderedDict
# import numpy as np
# import pandas as pd

from progressbar import ProgressBar

from Logger import get_now_str, init_colors, ansi_INTENSE, ansi_RED, ansi_GREEN, ansi_BLUE, ansi_CYAN, ansi_RESET



loop = asyncio.get_event_loop()


sentinel = object() # https://web.archive.org/web/20200221224620id_/http://effbot.org/zone/default-values.htm


is_dev_machine = (os.name == 'nt')
debugging = (is_dev_machine and sys.gettrace() is not None) and (1 == 1)  # debugging switches

if is_dev_machine or debugging:   # TODO!! refactor to a separate function called by the main module

  if False:    # TODO
    np_err_default = np.geterr()
    np.seterr(all='raise')  # https://stackoverflow.com/questions/15933741/how-do-i-catch-a-numpy-warning-like-its-an-exception-not-just-for-testing
    np.seterr(under=np_err_default["under"])
    # np.seterr(divide='raise')


  if True:

    import aiodebug.log_slow_callbacks
    # import aiodebug.monitor_loop_lag

    aiodebug.log_slow_callbacks.enable(120 if is_dev_machine else 10)  # https://stackoverflow.com/questions/65704785/how-to-debug-a-stuck-asyncio-coroutine-in-python
    # aiodebug.monitor_loop_lag.enable(statsd_client) # TODO

#/ if is_dev_machine or debugging:


if False and debugging:   # enable nested async calls so that async methods can be called from Immediate Window of Visual studio    # disabled: it is not compatible with Stampy wiki async stuff
  import nest_asyncio
  nest_asyncio.apply()


# https://stackoverflow.com/questions/28452429/does-gzip-compression-level-have-any-impact-on-decompression
# there's no extra overhead for the client/browser to decompress more heavily compressed gzip files
compresslevel = 9   # 6 is default level for gzip: https://linux.die.net/man/1/gzip
# https://github.com/ebiggers/libdeflate

data_dir = "data"



eps = 1e-15

BOM = codecs.BOM_UTF8

# https://stackoverflow.com/questions/36187349/python-regex-for-unicode-capitalized-words
#pLu = "[A-Z\u00C0-\u00D6\u00D8-\u00DE\u0100\u0102\u0104\u0106\u0108\u010A\u010C\u010E\u0110\u0112\u0114\u0116\u0118\u011A\u011C\u011E\u0120\u0122\u0124\u0126\u0128\u012A\u012C\u012E\u0130\u0132\u0134\u0136\u0139\u013B\u013D\u013F\u0141\u0143\u0145\u0147\u014A\u014C\u014E\u0150\u0152\u0154\u0156\u0158\u015A\u015C\u015E\u0160\u0162\u0164\u0166\u0168\u016A\u016C\u016E\u0170\u0172\u0174\u0176\u0178\u0179\u017B\u017D\u0181\u0182\u0184\u0186\u0187\u0189-\u018B\u018E-\u0191\u0193\u0194\u0196-\u0198\u019C\u019D\u019F\u01A0\u01A2\u01A4\u01A6\u01A7\u01A9\u01AC\u01AE\u01AF\u01B1-\u01B3\u01B5\u01B7\u01B8\u01BC\u01C4\u01C7\u01CA\u01CD\u01CF\u01D1\u01D3\u01D5\u01D7\u01D9\u01DB\u01DE\u01E0\u01E2\u01E4\u01E6\u01E8\u01EA\u01EC\u01EE\u01F1\u01F4\u01F6-\u01F8\u01FA\u01FC\u01FE\u0200\u0202\u0204\u0206\u0208\u020A\u020C\u020E\u0210\u0212\u0214\u0216\u0218\u021A\u021C\u021E\u0220\u0222\u0224\u0226\u0228\u022A\u022C\u022E\u0230\u0232\u023A\u023B\u023D\u023E\u0241\u0243-\u0246\u0248\u024A\u024C\u024E\u0370\u0372\u0376\u037F\u0386\u0388-\u038A\u038C\u038E\u038F\u0391-\u03A1\u03A3-\u03AB\u03CF\u03D2-\u03D4\u03D8\u03DA\u03DC\u03DE\u03E0\u03E2\u03E4\u03E6\u03E8\u03EA\u03EC\u03EE\u03F4\u03F7\u03F9\u03FA\u03FD-\u042F\u0460\u0462\u0464\u0466\u0468\u046A\u046C\u046E\u0470\u0472\u0474\u0476\u0478\u047A\u047C\u047E\u0480\u048A\u048C\u048E\u0490\u0492\u0494\u0496\u0498\u049A\u049C\u049E\u04A0\u04A2\u04A4\u04A6\u04A8\u04AA\u04AC\u04AE\u04B0\u04B2\u04B4\u04B6\u04B8\u04BA\u04BC\u04BE\u04C0\u04C1\u04C3\u04C5\u04C7\u04C9\u04CB\u04CD\u04D0\u04D2\u04D4\u04D6\u04D8\u04DA\u04DC\u04DE\u04E0\u04E2\u04E4\u04E6\u04E8\u04EA\u04EC\u04EE\u04F0\u04F2\u04F4\u04F6\u04F8\u04FA\u04FC\u04FE\u0500\u0502\u0504\u0506\u0508\u050A\u050C\u050E\u0510\u0512\u0514\u0516\u0518\u051A\u051C\u051E\u0520\u0522\u0524\u0526\u0528\u052A\u052C\u052E\u0531-\u0556\u10A0-\u10C5\u10C7\u10CD\u13A0-\u13F5\u1E00\u1E02\u1E04\u1E06\u1E08\u1E0A\u1E0C\u1E0E\u1E10\u1E12\u1E14\u1E16\u1E18\u1E1A\u1E1C\u1E1E\u1E20\u1E22\u1E24\u1E26\u1E28\u1E2A\u1E2C\u1E2E\u1E30\u1E32\u1E34\u1E36\u1E38\u1E3A\u1E3C\u1E3E\u1E40\u1E42\u1E44\u1E46\u1E48\u1E4A\u1E4C\u1E4E\u1E50\u1E52\u1E54\u1E56\u1E58\u1E5A\u1E5C\u1E5E\u1E60\u1E62\u1E64\u1E66\u1E68\u1E6A\u1E6C\u1E6E\u1E70\u1E72\u1E74\u1E76\u1E78\u1E7A\u1E7C\u1E7E\u1E80\u1E82\u1E84\u1E86\u1E88\u1E8A\u1E8C\u1E8E\u1E90\u1E92\u1E94\u1E9E\u1EA0\u1EA2\u1EA4\u1EA6\u1EA8\u1EAA\u1EAC\u1EAE\u1EB0\u1EB2\u1EB4\u1EB6\u1EB8\u1EBA\u1EBC\u1EBE\u1EC0\u1EC2\u1EC4\u1EC6\u1EC8\u1ECA\u1ECC\u1ECE\u1ED0\u1ED2\u1ED4\u1ED6\u1ED8\u1EDA\u1EDC\u1EDE\u1EE0\u1EE2\u1EE4\u1EE6\u1EE8\u1EEA\u1EEC\u1EEE\u1EF0\u1EF2\u1EF4\u1EF6\u1EF8\u1EFA\u1EFC\u1EFE\u1F08-\u1F0F\u1F18-\u1F1D\u1F28-\u1F2F\u1F38-\u1F3F\u1F48-\u1F4D\u1F59\u1F5B\u1F5D\u1F5F\u1F68-\u1F6F\u1FB8-\u1FBB\u1FC8-\u1FCB\u1FD8-\u1FDB\u1FE8-\u1FEC\u1FF8-\u1FFB\u2102\u2107\u210B-\u210D\u2110-\u2112\u2115\u2119-\u211D\u2124\u2126\u2128\u212A-\u212D\u2130-\u2133\u213E\u213F\u2145\u2160-\u216F\u2183\u24B6-\u24CF\u2C00-\u2C2E\u2C60\u2C62-\u2C64\u2C67\u2C69\u2C6B\u2C6D-\u2C70\u2C72\u2C75\u2C7E-\u2C80\u2C82\u2C84\u2C86\u2C88\u2C8A\u2C8C\u2C8E\u2C90\u2C92\u2C94\u2C96\u2C98\u2C9A\u2C9C\u2C9E\u2CA0\u2CA2\u2CA4\u2CA6\u2CA8\u2CAA\u2CAC\u2CAE\u2CB0\u2CB2\u2CB4\u2CB6\u2CB8\u2CBA\u2CBC\u2CBE\u2CC0\u2CC2\u2CC4\u2CC6\u2CC8\u2CCA\u2CCC\u2CCE\u2CD0\u2CD2\u2CD4\u2CD6\u2CD8\u2CDA\u2CDC\u2CDE\u2CE0\u2CE2\u2CEB\u2CED\u2CF2\uA640\uA642\uA644\uA646\uA648\uA64A\uA64C\uA64E\uA650\uA652\uA654\uA656\uA658\uA65A\uA65C\uA65E\uA660\uA662\uA664\uA666\uA668\uA66A\uA66C\uA680\uA682\uA684\uA686\uA688\uA68A\uA68C\uA68E\uA690\uA692\uA694\uA696\uA698\uA69A\uA722\uA724\uA726\uA728\uA72A\uA72C\uA72E\uA732\uA734\uA736\uA738\uA73A\uA73C\uA73E\uA740\uA742\uA744\uA746\uA748\uA74A\uA74C\uA74E\uA750\uA752\uA754\uA756\uA758\uA75A\uA75C\uA75E\uA760\uA762\uA764\uA766\uA768\uA76A\uA76C\uA76E\uA779\uA77B\uA77D\uA77E\uA780\uA782\uA784\uA786\uA78B\uA78D\uA790\uA792\uA796\uA798\uA79A\uA79C\uA79E\uA7A0\uA7A2\uA7A4\uA7A6\uA7A8\uA7AA-\uA7AE\uA7B0-\uA7B4\uA7B6\uFF21-\uFF3A\U00010400-\U00010427\U000104B0-\U000104D3\U00010C80-\U00010CB2\U000118A0-\U000118BF\U0001D400-\U0001D419\U0001D434-\U0001D44D\U0001D468-\U0001D481\U0001D49C\U0001D49E\U0001D49F\U0001D4A2\U0001D4A5\U0001D4A6\U0001D4A9-\U0001D4AC\U0001D4AE-\U0001D4B5\U0001D4D0-\U0001D4E9\U0001D504\U0001D505\U0001D507-\U0001D50A\U0001D50D-\U0001D514\U0001D516-\U0001D51C\U0001D538\U0001D539\U0001D53B-\U0001D53E\U0001D540-\U0001D544\U0001D546\U0001D54A-\U0001D550\U0001D56C-\U0001D585\U0001D5A0-\U0001D5B9\U0001D5D4-\U0001D5ED\U0001D608-\U0001D621\U0001D63C-\U0001D655\U0001D670-\U0001D689\U0001D6A8-\U0001D6C0\U0001D6E2-\U0001D6FA\U0001D71C-\U0001D734\U0001D756-\U0001D76E\U0001D790-\U0001D7A8\U0001D7CA\U0001E900-\U0001E921\U0001F130-\U0001F149\U0001F150-\U0001F169\U0001F170-\U0001F189]"




def set_data_dir(new_data_dir):
  global data_dir

  data_dir = new_data_dir

#/ def set_data_dir(new_data_dir):


def safeprint(text = "", is_pandas = False):

  if True or (is_dev_machine and debugging):

    screen_width = max(39, shutil.get_terminal_size((200, 50)).columns - 1)
    screen_height = max(19, shutil.get_terminal_size((200, 50)).lines - 1)

    if False:    # TODO
      np.set_printoptions(linewidth=screen_width, precision=2, floatmode="maxprec_equal", threshold=int((screen_height - 3) * screen_height / 2), edgeitems=int((screen_width - 3 - 4) / 5 / 2), formatter={ "bool": (lambda x: "T" if x else "_") }) # "maxprec_equal": Print at most precision fractional digits, but if every element in the array can be uniquely represented with an equal number of fewer digits, use that many digits for all elements.

    if is_pandas:
      import pd
      pd.set_option("display.precision", 2)
      pd.set_option("display.width", screen_width)        # pandas might fail to autodetect screen width when running under debugger
      pd.set_option("display.max_columns", screen_width)  # setting display.width is not sufficient for some  reason
      pd.set_option("display.max_rows", 100) 


  text = str(text).encode("utf-8", 'ignore').decode('ascii', 'ignore')

  if False:
    init_colors()
    print(ansi_CYAN + ansi_INTENSE + text + ansi_RESET)  # NB! need to concatenate ANSI colours not just use commas since otherwise the terminal.write would be called three times and write handler might override the colour for the text part
  else:
    print(text)

#/ def safeprint(text):


# need separate handling for error messages since they should not be sent to the terminal by the logger
def safeprinterror(text = "", is_pandas = False):

  if True or (is_dev_machine and debugging):

    screen_width = max(39, shutil.get_terminal_size((200, 50)).columns - 1)
    screen_height = max(19, shutil.get_terminal_size((200, 50)).lines - 1)

    if False:    # TODO
      np.set_printoptions(linewidth=screen_width, precision=2, floatmode="maxprec_equal", threshold=int((screen_height - 3) * screen_height / 2), edgeitems=int((screen_width - 3 - 4) / 5 / 2), formatter={ "bool": (lambda x: "T" if x else "_") }) # "maxprec_equal": Print at most precision fractional digits, but if every element in the array can be uniquely represented with an equal number of fewer digits, use that many digits for all elements.

    if is_pandas:
      import pd
      pd.set_option("display.precision", 2)
      pd.set_option("display.width", screen_width)        # pandas might fail to autodetect screen width when running under debugger
      pd.set_option("display.max_columns", screen_width)  # setting display.width is not sufficient for some reason
      pd.set_option("display.max_rows", 100) 


  text = str(text).encode("utf-8", 'ignore').decode('ascii', 'ignore')

  if False:
    init_colors()
    print(ansi_RED + ansi_INTENSE + text + ansi_RESET, file=sys.stderr)  # NB! need to concatenate ANSI colours not just use commas since otherwise the terminal.write would be called three times and write handler might override the colour for the text part
  else:
    print(text, file=sys.stderr)

#/ def safeprinterror(text):


def print_exception(msg):

  msg = "Exception during processing " + type(msg).__name__ + " : " + str(msg)  + "\n"

  safeprinterror(msg)

#/ def print_exception(msg):


# https://stackoverflow.com/questions/5849800/tic-toc-functions-analog-in-python
class Timer(object):

  def __init__(self, name=None, quiet=False):
    self.name = name
    self.quiet = quiet

  def __enter__(self):

    if not self.quiet and self.name:
      safeprint(get_now_str() + " : " + self.name + "...")

    self.tstart = time.time()

  def __exit__(self, type, value, traceback):

    elapsed = time.time() - self.tstart

    if not self.quiet:
      if self.name:
        safeprint(get_now_str() + " : " + self.name + " totaltime: {}".format(elapsed))
      else:
        safeprint(get_now_str() + " : " + "totaltime: {}".format(elapsed))
    #/ if not quiet:

#/ class Timer(object):


async def rename_temp_file(filename, make_backup = False):  # NB! make_backup is false by default since this operation would not be atomic

  max_tries = 20
  try_index = 1
  while True:

    try:

      if make_backup and os.path.exists(filename):

        if os.name == 'nt':   # rename is not atomic on windows and is unable to overwrite existing file. On UNIX there is no such problem
          if os.path.exists(filename + ".old"):
            if not os.path.isfile(filename + ".old"):
              raise ValueError("" + filename + ".old" + " is not a file")
            await aiofiles.os.remove(filename + ".old")

        await aiofiles.os.rename(filename, filename + ".old")

      #/ if make_backup and os.path.exists(filename):


      if os.name == 'nt':   # rename is not atomic on windows and is unable to overwrite existing file. On UNIX there is no such problem
        if os.path.exists(filename):
          if not os.path.isfile(filename):
            raise ValueError("" + filename + " is not a file")
          await aiofiles.os.remove(filename)

      await aiofiles.os.rename(filename + ".tmp", filename)

      return

    except Exception as ex:

      if try_index >= max_tries:
        raise

      try_index += 1
      safeprint("retrying temp file rename: " + filename)
      await asyncio.sleep(5)
      continue

    #/ try:

  #/ while True:

#/ def rename_temp_file(filename):


def init_logging(caller_filename = "", caller_name = "", log_dir = "logs", max_old_log_rename_tries = 10):

  from Logger import Logger, rename_log_file_if_needed


  logfile_name_prefix = caller_filename + ("_" if caller_filename else "")


  full_log_dir = os.path.join(data_dir, log_dir)
  if not os.path.exists(full_log_dir):
    os.makedirs(full_log_dir)


  rename_log_file_if_needed(os.path.join(full_log_dir, logfile_name_prefix + "standard_log.txt"), max_tries = max_old_log_rename_tries)
  rename_log_file_if_needed(os.path.join(full_log_dir, logfile_name_prefix + "error_log.txt"), max_tries = max_old_log_rename_tries)
  rename_log_file_if_needed(os.path.join(full_log_dir, logfile_name_prefix + "request_log.txt"), max_tries = max_old_log_rename_tries)


  if not isinstance(sys.stdout, Logger):
    sys.stdout = Logger(sys.stdout, os.path.join(full_log_dir, logfile_name_prefix + "standard_log.txt"), False)
    if caller_name == "__main__":
      sys.stdout.write("--- Main process " + caller_filename + " ---\n")
    else:
      sys.stdout.write("--- Subprocess process " + caller_filename + " ---\n")

  if not isinstance(sys.stderr, Logger):
    sys.stderr = Logger(sys.stdout, os.path.join(full_log_dir, logfile_name_prefix + "error_log.txt"), True) # NB! redirect stderr to stdout so that error messages are saved both in standard_log as well as in error_log


  if caller_name == '__main__':
    request_logger = Logger(terminal=None, logfile=os.path.join(full_log_dir, logfile_name_prefix + "request_log.txt"), is_error_log=False)
  else:
    request_logger = None

  return request_logger

#/ def init_logging():


async def read_file(filename, default_data = sentinel, quiet = False):
  """Reads a pickled file"""

  # https://web.archive.org/web/20200221224620id_/http://effbot.org/zone/default-values.htm
  if default_data is sentinel:
    default_data = {}

  fullfilename = os.path.join(data_dir, filename)

  if not os.path.exists(fullfilename + ".gz"):
    return default_data

  with Timer("file reading : " + filename, quiet):

    try:
      async with aiofiles.open(fullfilename + ".gz", 'rb', 1024 * 1024) as afh:
        compressed_data = await afh.read()    # TODO: decompress directly during reading and without using intermediate buffer for async data
        with io.BytesIO(compressed_data) as fh:   
          with gzip.open(fh, 'rb') as gzip_file:
            data = pickle.load(gzip_file)
    except FileNotFoundError:
      data = default_data

  #/ with Timer("file reading : " + filename):

  return data

#/ def read_file(filename):


async def save_file(filename, data, quiet = False, make_backup = False):
  """Writes to a pickled file"""

  haslen = hasattr(data, '__len__')
  message_template = "file saving {}" + (" num of all entries: {}" if haslen else "")
  message = message_template.format(filename, len(data) if haslen else 0)

  with Timer(message, quiet):

    fullfilename = os.path.join(data_dir, filename)

    if (1 == 1):    # enable async code

      async with aiofiles.open(fullfilename + ".gz.tmp", 'wb', 1024 * 1024) as afh:
        with io.BytesIO() as fh:    # TODO: compress directly during reading and without using intermediate buffer for async data
          with gzip.GzipFile(fileobj=fh, filename=filename, mode='wb', compresslevel=compresslevel) as gzip_file:
            pickle.dump(data, gzip_file)
            gzip_file.flush() # NB! necessary to prevent broken gz archives on random occasions (does not depend on input data)
          fh.flush()  # just in case
          buffer = bytes(fh.getbuffer())  # NB! conversion to bytes is necessary to avoid "BufferError: Existing exports of data: object cannot be re-sized"
          await afh.write(buffer)
        await afh.flush()

    else:   #/ if (1 == 0):

      with open(fullfilename + ".gz.tmp", 'wb', 1024 * 1024) as fh:
        with gzip.GzipFile(fileobj=fh, filename=filename, mode='wb', compresslevel=compresslevel) as gzip_file:
          pickle.dump(data, gzip_file)
          gzip_file.flush() # NB! necessary to prevent broken gz archives on random occasions (does not depend on input data)
        fh.flush()  # just in case

    #/ if (1 == 0):

    await rename_temp_file(fullfilename + ".gz", make_backup)

  #/ with Timer("file saving {}, num of all entries: {}".format(filename, len(cache))):

#/ def save_file(filename, data):


async def read_raw(filename, default_data = None, quiet = False):
  """Reads a raw file"""

  fullfilename = os.path.join(data_dir, filename)

  if not os.path.exists(fullfilename):
    return default_data

  with Timer("raw file reading : " + filename, quiet):

    try:
      async with aiofiles.open(fullfilename, 'rb', 1024 * 1024) as afh:
        data = await afh.read() 
    except FileNotFoundError:
      data = default_data

  #/ with Timer("file reading : " + filename):

  return data

#/ def read_raw(filename):


async def read_txt(filename, default_data = None, quiet = False, encoding="utf-8"):
  """Reads from a text file"""

  fullfilename = os.path.join(data_dir, filename)

  if not os.path.exists(fullfilename):
    return default_data


  message_template = "file reading {}"
  message = message_template.format(filename)

  with Timer(message, quiet):

    try:
      async with aiofiles.open(fullfilename, 'r', 1024 * 1024, encoding=encoding) as afh:
        data = await afh.read()

    except FileNotFoundError:
      data = default_data

  #/ with Timer(message, quiet):

  return data

#/ async def read_txt(filename, quiet = False):


async def save_txt(filename, str, quiet = False, make_backup = False, append = False, use_bom = True, encoding="utf-8"):
  """Writes to a text file"""

  message_template = "file saving {} num of characters: {}"
  message = message_template.format(filename, len(str))

  with Timer(message, quiet):

    fullfilename = os.path.join(data_dir, filename)

    if (1 == 1):    # enable async code

      async with aiofiles.open(fullfilename + ("" if append else ".tmp"), 'at' if append else 'wt', 1024 * 1024, encoding=encoding) as afh:    # wt format automatically handles line breaks depending on the current OS type
        if use_bom:
          await afh.write(codecs.BOM_UTF8.decode("utf-8"))    # TODO: encoding
        await afh.write(str)
        await afh.flush()

    else:   #/ if (1 == 0):

      with open(fullfilename + ("" if append else ".tmp"), 'at' if append else 'wt', 1024 * 1024, encoding=encoding) as fh:    # wt format automatically handles line breaks depending on the current OS type
        if use_bom:
          # fh.write(codecs.BOM_UTF8 + str.encode("utf-8", "ignore"))
          fh.write(codecs.BOM_UTF8.decode("utf-8"))    # TODO: encoding
        fh.write(str)
        fh.flush()  # just in case

    if not append:
      await rename_temp_file(fullfilename, make_backup)

  #/ with Timer("file saving {}, num of all entries: {}".format(filename, len(cache))):

#/ def save_txt(filename, data):


def strtobool(val, allow_additional_values=[]):

  val = val.lower() if val else ""
  if val in allow_additional_values:
      return val
  elif val in ('y', 'yes', 't', 'true', 'on', '1'):
      return True
  elif val in ('n', 'no', 'f', 'false', 'off', '0'):
      return False
  else:
      raise ValueError(f"invalid value passed to strtobool: {val}")

#/ def strtobool(val):


def remove_quotes(text):

  return text.replace("'", "").replace('"', '')   # TODO: remove only outermost quotes

#/ def remove_quotes(text):


def get_type_full_name(arg):

  t = type(arg)
  return t.__module__ + "." + t.__name__

#/ def get_type_full_name(arg):


def convert_arg_to_cache_key(arg):

  t = get_type_full_name(arg)
  if t == "tiktoken.core.Encoding":
    return t + ":" + arg.name
  else:
    return arg

#/ def convert_arg_to_cache_key(args):


def convert_args_to_cache_key(args):

  result = []
  for arg in args:
    converted = convert_arg_to_cache_key(arg)
    result.append(converted)

  return result

#/ def convert_args_to_cache_key(args):


def convert_kwargs_to_cache_key(kwargs):

  result = OrderedDict()
  for key, arg in kwargs.items():
    converted = convert_arg_to_cache_key(arg)
    result[key] = converted

  return result

#/ def convert_args_to_cache_key(args):


async def async_cached(cache_version, func, *args, **kwargs):

  result = await async_cached_worker(False, cache_version, func, *args, **kwargs)
  return result


async def peek_async_cached(cache_version, func, *args, **kwargs):

  result = await async_cached_worker(True, cache_version, func, *args, **kwargs)
  return result


async def async_cached_worker(peek_only, cache_version, func, *args, **kwargs):

  enable_cache = (cache_version is not None)

  if enable_cache:

    # NB! this cache key and the cache will not contain the OpenAI key, so it is safe to publish the cache files
    kwargs_ordered = OrderedDict(sorted(kwargs.items()))
    cache_key = OrderedDict([
      ("args", convert_args_to_cache_key(args)),
      ("kwargs", convert_kwargs_to_cache_key(kwargs_ordered))
    ])
    params_json = json_tricks.dumps(cache_key).encode("utf-8")   # json_tricks preserves dictionary orderings
    cache_key = hashlib.sha512(params_json).digest()
    # use base32 coding, not base16/hex, in order for having shorter filenames   
    # replace padding char "=" with "0" char which is not in the base32 alphabet   
    # base36 would be even better, but I did not find a good library for that
    cache_key = base64.b32encode(cache_key).decode("utf8").lower().replace("=", "0") 
    cache_key = "func=" + func.__name__ + "-ver=" + str(cache_version) + "-args=" + cache_key

    fulldirname = os.path.join(data_dir, "cache")
    os.makedirs(fulldirname, exist_ok = True)

    cache_filename = os.path.join("cache", "cache_" + cache_key + ".dat")
    response = await read_file(cache_filename, default_data = None, quiet = True)

  else:   #/ if enable_cache:

    response = None


  if response is None and not peek_only:

    if asyncio.iscoroutinefunction(func):
      response = await func(*args, **kwargs)
    else:
      response = func(*args, **kwargs)

    if enable_cache:
      await save_file(cache_filename, response, quiet = True)   # TODO: save arguments in cache too and compare it upon cache retrieval

  #/ if response is None and not peek_only:


  return response

#/ async def async_cached():


class RobustProgressBar(ProgressBar):

  def __init__(self, *args, initial_value=0, disable=False, granularity=1, **kwargs):

    self.disable = disable
    self.granularity = granularity
    self.prev_value = initial_value
    super(RobustProgressBar, self).__init__(*args, initial_value=initial_value, **kwargs)


  def __enter__(self):

    if not self.disable:
      try:
        super(RobustProgressBar, self).__enter__()
      except Exception:  # TODO: catch only console write related exceptions
        pass

    return self


  def __exit__(self, type, value, traceback):

    if not self.disable:
      try:
        super(RobustProgressBar, self).__exit__(type, value, traceback)
      except Exception:  # TODO: catch only console write related exceptions
        pass

    return


  def update(self, value=None, *args, force=False, **kwargs):

    if not self.disable:
      try:
        if (
          force 
          or (value is not None and value - self.prev_value >= self.granularity)
        ):  # avoid too frequent console updates which would slow down the computation

          if value is not None:
            self.prev_value = value
          super(RobustProgressBar, self).update(value, *args, force=force, **kwargs)

      except Exception:  # TODO: catch only console write related exceptions
        pass

    return

  #def _blackHoleMethod(*args, **kwargs):
  #  return

  #def __getattr__(self, attr):
  #
  #  if not self.disable:
  #    return super(RobustProgressBar, self).__getattr__(attr)
  #  else:
  #    return self._blackHoleMethod

#/ class RobustProgressBar(ProgressBar):


left_brac = r'({<\['
right_brac = r')}>\]'

left_brac_or_punc = r'[.,:;!?' + left_brac + '\/\-]'  # NB! / or - IS included here
left_brac_or_punc_except_dot_and_comma = r'[:;!?' + left_brac + '\/\-]'  # NB! / or - IS included here
right_brac_or_punc = r'[.,:;!?' + right_brac + ']'     # NB! / or - IS NOT included here

# https://stackoverflow.com/questions/17327765/exclude-characters-from-a-character-class
alpha_except_left_brac_or_punc = r'((?!' + left_brac_or_punc + ')\S)'
alpha_except_right_brac_or_punc = r'((?!' + right_brac_or_punc + ')\S)'

alphas_except_left_brac_or_punc_at_start = alpha_except_left_brac_or_punc + r'\S*'
alphas_except_right_brac_or_puncs_at_end = r'\S*' + alpha_except_right_brac_or_punc

space_or_left_brac_or_punc = r'(' + left_brac_or_punc + r'|\s)'    # cannot add |^ since "A lookbehind assertion has to be fixed width"
space_or_left_brac_or_punc_except_dot_and_comma = r'(' + left_brac_or_punc_except_dot_and_comma + r'|\s)'    # cannot add |^ since "A lookbehind assertion has to be fixed width"
space_or_right_brac_or_punc = r'(' + right_brac_or_punc + r'|\s)'  # could add |$ but not adding for consistency with space_or_left_brac_or_punc

lookbehind_space_or_left_brac_or_punc = r'(?<=' + space_or_left_brac_or_punc + r')'
lookbehind_space_or_left_brac_or_punc_except_dot_and_comma = r'(?<=' + space_or_left_brac_or_punc_except_dot_and_comma + r')'
lookahead_space_or_right_brac_or_punc = r'(?=' + space_or_right_brac_or_punc + r')'

# (?=(\d+))\7 or (?=(?P<dd>\d+))(?P=dd) ensures that the digit matching in that regex part is greedy and atomic. See https://stackoverflow.com/questions/48611167/prevent-backtracking-on-regex-to-find-non-comment-lines-not-starting-with-inden and https://www.regular-expressions.info/named.html
greedy_atomic_digits1 = r'(?=(?P<greedy_atomic_digits1>\d+))(?P=greedy_atomic_digits1)'
greedy_atomic_digits2 = r'(?=(?P<greedy_atomic_digits2>\d+))(?P=greedy_atomic_digits2)'

space_except_newlines = r'[^\S\r\n]'    # Python does not support \h

# https://chatgpt.com/share/3d6112bd-4f51-4898-a87f-470e4d30df40
#
# Hyphen-Minus (-)
# Unicode: U+002D
# Description: The standard hyphen, used in most keyboards. It is the most commonly used dash-like character in compound names, such as in double-barreled surnames (e.g., "Smith-Jones").
#
#Non-Breaking Hyphen (‑)
#Unicode: U+2011
#Description: Similar to the standard hyphen but prevents a line break at its position. It's useful in ensuring that parts of a name are not separated across lines in text formatting.
#
#En Dash (–)
#Unicode: U+2013
#Description: Slightly longer than a hyphen. It's used in some typographical traditions for compound names, especially where each part of the compound is itself multi-part or has an open space (e.g., "Jean–Luc Picard").
dash_in_names_re = r'[\u002D\u2011\u2013]'

single_dash_in_name_or_spaces_except_newlines = r'(' + dash_in_names_re + '|' + space_except_newlines + '+)'

# regex.DOTALL flag is not needed in these regexes

topleveldomains = ['com', 'org', 'net', 'edu', 'gov', 'int', 'mil', 'me', 'io', 'ai', 'ru', 'co.uk']     # TODO: add more top-level domains here
topleveldomains = [regex.escape(x) for x in topleveldomains]
topleveldomains = '|'.join(topleveldomains)


http_re     = regex.compile(
  lookbehind_space_or_left_brac_or_punc 
  + r'(http|https|ftp)://' + alphas_except_right_brac_or_puncs_at_end                       # https://whatever
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)
url_like_re = regex.compile(
  lookbehind_space_or_left_brac_or_punc    
  + alphas_except_left_brac_or_punc_at_start + r'[.]\S+/' + alphas_except_right_brac_or_puncs_at_end   # domain.xyz/folder 
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)
domain_re   = regex.compile(
  lookbehind_space_or_left_brac_or_punc
  + alphas_except_left_brac_or_punc_at_start + r'[.](' + topleveldomains + ')' # domain.com
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)
www_re      = regex.compile(
  lookbehind_space_or_left_brac_or_punc 
  + r'www[.]' + alphas_except_right_brac_or_puncs_at_end                                    # www.domain.xyz   
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)


email_re    = regex.compile(
  lookbehind_space_or_left_brac_or_punc    
  + alphas_except_left_brac_or_punc_at_start + r'@\S+[.]' + alphas_except_right_brac_or_puncs_at_end   # email@domain.xyz  
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)
at_gmail_re = regex.compile(
  lookbehind_space_or_left_brac_or_punc     # TODO: add more mail domains or make it configurable via config file
  + r'at\s+(gmail|hotmail)(\s+dot\s+com)?'                                                # at gmail, at hotmail
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)


# see also https://stackoverflow.com/questions/16699007/regular-expression-to-match-standard-10-digit-phone-number

# https://chatgpt.com/share/3d6112bd-4f51-4898-a87f-470e4d30df40
#
# Hyphen-Minus (-)
# Unicode: U+002D
# Description: The standard hyphen, used in most keyboards. It is the most commonly used dash-like character in compound names, such as in double-barreled surnames (e.g., "Smith-Jones").
#
# Figure Dash (‒)
# Unicode: U+2012
# Description: Similar in width to a hyphen. It's used primarily in numerical contexts, like phone numbers, rather than in names.
single_phone_number_dash = r'[\u002D\u2012]'

phone_without_dots_re    = regex.compile(   
  lookbehind_space_or_left_brac_or_punc      # NB! here we exlude . and , from lookbehind
  # NB! here we do not use \s but space_except_newlines instead. Newlines should not be inside phone numbers.
  + r'(([+]|00)?[1-9]|[(]([+]|00)?[1-9]\d*[)])(\d+|(((' + single_phone_number_dash + r'|' + space_except_newlines + r')*|(' + single_phone_number_dash + r'|' + space_except_newlines + r')*[(]' + space_except_newlines + r'*\d+' + space_except_newlines + r'*[)](' + single_phone_number_dash + r'|' + space_except_newlines + r')*)' + greedy_atomic_digits1 + r')){2,}'  # +372 58 058 134, 00372 58 058 134, (+372) 58 058 134, +1 (800) 58 058 134
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)

phone_with_dots_re    = regex.compile(   
  lookbehind_space_or_left_brac_or_punc     
  # NB! here we do not use \s but space_except_newlines instead. Newlines should not be inside phone numbers.
  + r'(([+]|00)?[1-9]|[(]([+]|00)?[1-9]\d*[)])(\d+|((([.]|' + space_except_newlines + r')+|([.]|' + space_except_newlines + r')+[(]' + space_except_newlines + r'*\d+' + space_except_newlines + r'*[)]([.]|' + space_except_newlines + r')+)' + greedy_atomic_digits2 + r')){2,}'  # +372 58 058 134, 00372 58 058 134, (+372) 58 058 134, +1 (800) 58 058 134
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)


# see also https://en.wikipedia.org/wiki/Decimal_separator

number_without_spaces_with_dot_or_comma_re   = regex.compile(
  lookbehind_space_or_left_brac_or_punc
  + r'[+\-]?(\d[.,]\d+e[+\-]?[1-9]\d*|\d+([\'.,]\d{3})+([.,]\d+)?|\d+([\'.,]\d{3})*[.,]\d+)'   # -1.23e45  -1'234'567.89   -1'234'567,89   -1,234,567.89   -1.234.567,89   -1'234'567
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)

number_without_spaces_without_dot_or_comma_re   = regex.compile(
  lookbehind_space_or_left_brac_or_punc
  + r'[+\-]?\d+'   # -123
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)

number_with_spaces_re   = regex.compile(
  lookbehind_space_or_left_brac_or_punc
  + r'[+\-]?\d+(' + space_except_newlines + r'\d{3})+([.,]\d+)?'   #-1 234 567,89
  + lookahead_space_or_right_brac_or_punc,
  regex.IGNORECASE
)


#title_cased_words_re   = re.compile(
#  lookbehind_space_or_left_brac_or_punc   # NB! do not anonymise upper-cased words
#  + pLu + r'\w+(' + single_dash_in_name_or_spaces_except_newlines + r'(' + pLu + r'\w+|' + pLu + r'[.]?))*' + single_dash_in_name_or_spaces_except_newlines + pLu + r'\w+'   # Abc D E. Fgh Ijk
#  + lookahead_space_or_right_brac_or_punc  # ,
#  # re.IGNORECASE
#)

# TODO: handle more diacritics besides '
title_cased_words_re   = regex.compile(
  lookbehind_space_or_left_brac_or_punc   # NB! do not anonymise upper-cased words    # NB! allow ' character in the words
  + r'\p{Lu}[\'\p{Ll}]+(' + single_dash_in_name_or_spaces_except_newlines + r'(\p{Lu}[\'\p{Ll}]+|\p{Lu}[.]?))*' + single_dash_in_name_or_spaces_except_newlines + r'\p{Lu}[\'\p{Ll}]+'   # Abc D E. Fgh Ijk
  + lookahead_space_or_right_brac_or_punc   # ,
  # regex.IGNORECASE
)


# TODO
#percent_dollar_eur_pound_re  = regex.compile(
#  lookbehind_space_or_left_brac_or_punc 
#  + r'[0-9,.\']*[0-9]\s*(%|\$|usd|€|eur|£)'                                               # 12 %, 12 $, 12 eur 
#  + lookahead_space_or_right_brac_or_punc,
#  regex.IGNORECASE
#)
