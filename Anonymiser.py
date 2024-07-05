# -*- coding: utf-8 -*-

#
# Author: Roland Pihlakas, 2023 - 2024
#
# roland@simplify.ee
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#


if __name__ == '__main__':
  print("Starting...")


import os
import sys
import regex
from collections import defaultdict
from configparser import ConfigParser
import pandas as pd                 # .csv, xls, xlsx, xlsb, .odp, .ods, .odt

from lingua import Language, LanguageDetectorBuilder


from Utilities import data_dir, init_logging, safeprint, print_exception, loop, debugging, is_dev_machine, data_dir, Timer, read_file, save_file, read_txt, save_txt, strtobool, remove_quotes, async_cached, RobustProgressBar, space_except_newlines
import Anonymise


# if __name__ == "__main__":
#   init_logging(os.path.basename(__file__), __name__, max_old_log_rename_tries = 1)


if __name__ == "__main__":
  os.chdir(os.path.dirname(os.path.realpath(__file__)))

if is_dev_machine:
  from pympler import asizeof



def get_config():

  config = ConfigParser(inline_comment_prefixes=("#", ";"))  # by default, inline comments were not allowed
  config.read('Anonymiser.ini')

  config_section = "Anonymiser"


  anonymise_names = strtobool(remove_quotes(config.get(config_section, "AnonymiseNames", fallback="false")))
  anonymise_numbers = strtobool(remove_quotes(config.get(config_section, "AnonymiseNumbers", fallback="false")))
  anonymise_dates = strtobool(remove_quotes(config.get(config_section, "AnonymiseDates", fallback="false")))
  anonymise_titles_of_work = strtobool(remove_quotes(config.get(config_section, "AnonymiseTitlesOfWork", fallback="false")))

  anonymise_title_cased_word_sequences = strtobool(remove_quotes(config.get(config_section, "AnonymiseTitleCasedWordSequences", fallback="false")))
  anonymise_urls = strtobool(remove_quotes(config.get(config_section, "AnonymiseUrls", fallback="false")))
  anonymise_emails = strtobool(remove_quotes(config.get(config_section, "AnonymiseEmails", fallback="false")))
  anonymise_phone_numbers = strtobool(remove_quotes(config.get(config_section, "AnonymisePhoneNumbers", fallback="false")))

  named_entity_recognition_model = remove_quotes(config.get(config_section, "NamedEntityRecognitionModel", fallback="en_core_web_sm")).strip()
  use_only_numeric_replacements = strtobool(remove_quotes(config.get(config_section, "UseOnlyNumericReplacements", fallback="false")))

  encoding = remove_quotes(config.get(config_section, "Encoding", fallback="utf-8")).strip()

  csv_delimiter = remove_quotes(config.get(config_section, "CsvDelimiter", fallback=",")).strip()
  csv_anonymise_header = strtobool(remove_quotes(config.get(config_section, "CsvAnonymiseHeader", fallback="false")))

  csv_quotechar = remove_quotes(config.get(config_section, "CsvQuoteChar", fallback='"')).strip()
  if csv_quotechar == "default" or csv_quotechar == "double":
    csv_quotechar = '"'
  elif csv_quotechar == "single":
    csv_quotechar = "'"

  csv_doublequote = strtobool(remove_quotes(config.get(config_section, "CsvDoubleQuote", fallback="true")))

  csv_escapechar = remove_quotes(config.get(config_section, "CsvEscapeChar", fallback=",")).strip()
  if csv_escapechar == "default" or csv_escapechar == "none":
    csv_escapechar = None
  elif csv_escapechar == "double":
    ccsv_escapechar = '"'
  elif csv_escapechar == "single":
    csv_escapechar = "'"


  result = { 
    "anonymise_names": anonymise_names,
    "anonymise_numbers": anonymise_numbers,
    "anonymise_dates": anonymise_dates,
    "anonymise_titles_of_work": anonymise_titles_of_work,

    "anonymise_title_cased_word_sequences": anonymise_title_cased_word_sequences,
    "anonymise_urls": anonymise_urls,
    "anonymise_emails": anonymise_emails,
    "anonymise_phone_numbers": anonymise_phone_numbers,

    "named_entity_recognition_model": named_entity_recognition_model,
    "use_only_numeric_replacements": use_only_numeric_replacements,

    "encoding": encoding,

    "csv_anonymise_header": csv_anonymise_header,
    "csv_delimiter": csv_delimiter,
    "csv_quotechar": csv_quotechar,
    "csv_doublequote": csv_doublequote,
    "csv_escapechar": csv_escapechar,
  }

  return result

#/ get_config()


def anonymise_uncached(user_input, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, anonymise_title_cased_word_sequences, anonymise_urls, anonymise_emails, anonymise_phone_numbers, ner_model, use_only_numeric_replacements = False, state = None):

  return Anonymise.anonymise(user_input, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, anonymise_title_cased_word_sequences, anonymise_urls, anonymise_emails, anonymise_phone_numbers, ner_model, use_only_numeric_replacements=use_only_numeric_replacements, state=state)

#/ def anonymise_uncached()


async def anonymise(config, user_input, ner_model, state = None, enable_cache = False):


  anonymise_names = config.get("anonymise_names")
  anonymise_numbers = config.get("anonymise_numbers")
  anonymise_dates = config.get("anonymise_dates")
  anonymise_titles_of_work = config.get("anonymise_titles_of_work")

  anonymise_title_cased_word_sequences = config.get("anonymise_title_cased_word_sequences")
  anonymise_urls = config.get("anonymise_urls")
  anonymise_emails = config.get("anonymise_emails")
  anonymise_phone_numbers = config.get("anonymise_phone_numbers")

  use_only_numeric_replacements = config.get("use_only_numeric_replacements")


  # Spacy's NER is not able to see names separated by multiple spaces as a single name. Newlines in names are fortunately ok though. Tabs are ok too, though they will still be replaced in the following regex.
  # Replace spaces before caching so that changes in spacing do not require cache update
  user_input = regex.sub(space_except_newlines + r"+", " ", user_input)    # replace all repeating whitespace which is not newline with a single space - https://stackoverflow.com/questions/3469080/match-whitespace-but-not-newlines


  cache_version = 2

  # TODO remove cache functions?
  result = await async_cached(cache_version if enable_cache else None, anonymise_uncached, user_input, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, anonymise_title_cased_word_sequences, anonymise_urls, anonymise_emails, anonymise_phone_numbers, ner_model, use_only_numeric_replacements=use_only_numeric_replacements, state=state)

  return result

#/ async def anonymise():


spacy_loaded = False

def choose_ner_model(detector, user_input, default_ner_model):
  global spacy_loaded

  language = detector.detect_language_of(user_input)
  if language is None:
    if user_input.strip() != "" and len(user_input.strip()) > 1 and not user_input.strip().isnumeric():
      qqq = True    # for debugging   # can be a date
    return default_ner_model

  iso_code = language.iso_code_639_1.name.lower()

  ner_model_parts = default_ner_model.split("_")
  ner_model_language = ner_model_parts[0]
  ner_model_size = ner_model_parts[3]


  if iso_code == ner_model_language:

    ner_model = default_ner_model

  else:   # adapt the spacy model name depending on the language, also check whether spacy's alternate NER language model has same sized model available that was specified in the default NER model

    if not spacy_loaded:
      with Timer("Loading Spacy"):
        import spacy.util
        import spacy.cli    # spacy.cli.download(spacy_model_name)  # NB! here spacy.cli.download is a function
        from spacy.cli.download import get_compatibility    # NB! here spacy.cli.download is a module
        spacy_loaded = True

    available_models = spacy.util.get_installed_models()
    compatibility = get_compatibility()



    if iso_code == "en":
      ner_model = "en_core_web_" + ner_model_size

    elif iso_code == "ru":
      if ner_model_size == "trf":
        ner_model_size = "lg"    # Russian model does not have trf size available, lets use lg instead, it is about as good

      ner_model = "ru_core_news_" + ner_model_size

    else:
      # TODO: add more language models
      ner_model = default_ner_model    # not implemented, lets hope it works out. If not, the user needs to configure things manually

  #/ if ner_model_language != iso_code:


  return ner_model

#/ choose_ner_model(detector, user_input, ner_model)


async def anonymiser(argv = None):


  argv = argv if argv else sys.argv


  config = get_config()


  # read user input
  input_filename = argv[1] if len(argv) > 1 else None
  input_filename_orig = input_filename
  if input_filename:
    input_filename = os.path.join("..", input_filename)   # the applications default data location is in folder "data", but in case of user provided files lets expect the files in the same folder than the main script
  else:    
    input_filename = "test_input_en.txt"


  input_filename_parts = os.path.splitext(input_filename)
  file_name_stem = input_filename_parts[0]
  file_extension = input_filename_parts[1]


  output_filename = argv[2] if len(argv) > 2 else None
  if output_filename:
    output_filename = os.path.join("..", output_filename)
  else:
    output_filename = file_name_stem + "_anonymised" + file_extension


  if file_extension == ".tsv":  # TODO: support for compressed CSV files. Pandas supports it by default.
    is_table = True

    encoding = config.get("encoding")
    csv_anonymise_header = config.get("csv_anonymise_header")

    fullfilename = os.path.join(data_dir, input_filename)
    user_input = pd.read_csv(fullfilename, delimiter="\t", dtype=str, na_filter=False, encoding=encoding, encoding_errors="ignore", on_bad_lines="warn", header=None if csv_anonymise_header else 0)  

  elif file_extension == ".csv":  # TODO: support for compressed CSV files. Pandas supports it by default.
    is_table = True

    encoding = config.get("encoding")
    csv_anonymise_header = config.get("csv_anonymise_header")

    csv_delimiter = config.get("csv_delimiter")
    csv_quotechar = config.get("csv_quotechar")
    csv_doublequote = config.get("csv_doublequote")
    csv_escapechar = config.get("csv_escapechar")

    # TODO: add "quoting" parameter as well?
    # TODO: add "dialect" parameter? (But note: .to_csv() does not have support for dialect parameter).

    fullfilename = os.path.join(data_dir, input_filename)
    user_input = pd.read_csv(fullfilename, delimiter=csv_delimiter, dtype=str, na_filter=False, quotechar=csv_quotechar, doublequote=csv_doublequote, escapechar=csv_escapechar, encoding=encoding, encoding_errors="ignore", on_bad_lines="warn", header=None if csv_anonymise_header else 0)

  else:
    is_table = False

    encoding = config.get("encoding")

    user_input = (await read_txt(input_filename, quiet = True, encoding=encoding))

  assert user_input is not None, "Input file not found"


  languages = [Language.ENGLISH, Language.RUSSIAN]    # TODO: config parameter
  detector = LanguageDetectorBuilder.from_languages(*languages).build()


  ner_model = config.get("named_entity_recognition_model")


  if not is_table:

    language_ner_model = choose_ner_model(detector, user_input, ner_model)

    user_input, anonymise_state = await anonymise(config, user_input, language_ner_model, enable_cache=False)
  
    await save_txt(output_filename, user_input, encoding=encoding)

    # TODO: write anonymise_state to file, or at least the replacements dictionary

  else:
    anonymise_state = None

    # TODO: cache the result of processing whole CSV file
    columns = user_input.columns.tolist()
    with RobustProgressBar(max_value=len(user_input)) as bar:
      for row_index, (pd_index, row) in enumerate(user_input.iterrows()):
        for col in columns:

          cell_in = row[col]
          
          language_ner_model = choose_ner_model(detector, cell_in, ner_model)

          cell_out, anonymise_state = await anonymise(config, cell_in, language_ner_model, state=anonymise_state, enable_cache=False)    # NB! cannot use cache here since the replacements need to be shared over all cells
          if cell_in != cell_out:
            user_input.loc[pd_index, col] = cell_out

        bar.update(row_index + 1)

    # TODO: make applymap work with async anonymise function, or use a monolithic cache and load cache outside of loop
    # user_input = await user_input.applymap(async lambda x: await anonymise(config, x, language_ner_model, state=anonymise_state, enable_cache=False))


    output_filename = os.path.join(data_dir, output_filename)

    if file_extension == ".tsv":
      user_input.to_csv(output_filename, sep="\t", header=not csv_anonymise_header, index=False, encoding=encoding) # if csv_anonymise_header is True, then header is already part of the data. Setting header=True in this case would result in an extra header row consisting of increasing integer numbers.

    else:
      user_input.to_csv(output_filename, sep=csv_delimiter, header=not csv_anonymise_header, index=False, encoding=encoding, quotechar=csv_quotechar, doublequote=csv_doublequote, escapechar=csv_escapechar) # if csv_anonymise_header is True, then header is already part of the data. Setting header=True in this case would result in an extra header row consisting of increasing integer numbers.

    # TODO: write anonymise_state to file, or at least the replacements dictionary

  #/ if not is_table:


  return

#/ async def anonymiser():


async def loop_anonymiser():    # for debugging

  while True:
    await anonymiser()
    print("Press any key to process again")
    input()

#/ async def loop_anonymiser():


if __name__ == '__main__':
  # loop.run_until_complete(loop_anonymiser())
  loop.run_until_complete(anonymiser())


