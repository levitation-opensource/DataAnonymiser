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


import regex
import string
from collections import namedtuple


from Utilities import Timer, email_re, at_gmail_re, http_re, url_like_re, www_re, domain_re, phone_without_dots_re, phone_with_dots_re, number_without_spaces_with_dot_or_comma_re, number_without_spaces_without_dot_or_comma_re, number_with_spaces_re, title_cased_words_re, left_brac


ner_cache = {}
spacy_loaded = False
# spacy = None


def get_segments_from_ner(phase, user_input, reserved_entities_dict, ner_entities, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, ner_model):

  prev_ent_end = 0
  for segment in ner_entities.ents:

    text_original = segment.text
    label = segment.label_
    start_char = segment.start_char
    end_char = segment.end_char

    text_normalised = regex.sub(r"\s+", " ", text_original) # normalise the dictionary keys so that same entity with different space formats gets same replacement

    if phase == 0 and text_normalised in reserved_entities_dict: # Spacy detects texts like "Location C" as entities
      replacement = None    # TODO: yield here so that the "Location C" does not become later part of some longer title cased sequence that will be replaced by regex? Happens for example with the words "Threshold Glasgow Day Opportunities"

    elif label == "PERSON":
      replacement = "Person" if anonymise_names else None
    elif label == "NORP":
      replacement = "Group" if anonymise_names else None
    elif label == "FAC":
      replacement = "Building" if anonymise_names else None
    elif label == "ORG":
      replacement = "Organisation" if anonymise_names else None
    elif label == "GPE":
      replacement = "Area" if anonymise_names else None
    elif label == "LOC":
      replacement = "Location" if anonymise_names else None
    elif label == "PRODUCT":
      replacement = None  # "Product"   # TODO
    elif label == "EVENT":
      replacement = "Event" if anonymise_names else None
    elif label == "WORK_OF_ART":
      replacement = "Title of Work" if anonymise_titles_of_work else None  
    elif label == "LAW":
      replacement = None  # "Law"
    elif label == "LANGUAGE":
      replacement = "Language" if anonymise_names else None
    elif label == "DATE":
      replacement = (
                        (
                            "Calendar Date"
                            if regex.search(r"[1-9][0-9]{3}", text_normalised) is not None    # detect whether the text contains 4-place number
                            else (
                                "Age"
                                if ner_model[:3] == "en_"   # TODO: support for other languages
                                and regex.search(r"\sOLD", text_normalised, regex.IGNORECASE)    
                                else "Calendar Date or Age"
                            )
                        ) 
                        if anonymise_dates 
                        and regex.search(r"(\d|\s)", text_normalised) is not None   # recognise only calendar dates which contain at least one number, not phrases like "a big day", "today", etc
                        else None
                    )
    elif label == "TIME":
      replacement = None  # "Time"
    elif label == "PERCENT":
      replacement = None  # "Percent"
    elif label == "MONEY":
      replacement = "Money Amount" if anonymise_numbers else None
    elif label == "QUANTITY":
      replacement = "Quantity" if anonymise_numbers else None
    elif label == "ORDINAL":
      replacement = None  # "Ordinal"
    elif label == "CARDINAL":
      replacement = (
                        "Number"
                        if anonymise_numbers 
                        # and len(text_normalised) > 2  #    # do not anonymise short numbers since they are likely ordinals too
                        and regex.search(r"(\d|\s)", text_normalised) is not None   # if it is a one-word textual representation of a number then do not normalise it. It might be phrase like "one-sided" etc, which is actually not a number
                        else None
                    )

    else:
      replacement = None


    if replacement is None:
      continue   # aggregate all non-replaced texts into one segment


    if prev_ent_end < start_char:
      yield {
        "text": user_input[prev_ent_end:start_char],
        "label": None,
        "start_char": prev_ent_end,
        "end_char": start_char,
        "replacement": None,
        "text_normalised": None,
      }

    yield {
      "text": text_original,
      "label": label,
      "start_char": start_char,
      "end_char": end_char,
      "replacement": replacement,
      "text_normalised": text_normalised,
    }

    prev_ent_end = end_char

  #/ for word in entities.ents:

  if prev_ent_end < len(user_input):
    yield {
      "text": user_input[prev_ent_end:],
      "label": None,
      "start_char": prev_ent_end,
      "end_char": len(user_input),
      "replacement": None,
      "text_normalised": None,
    }

#/ def get_segments_from_ner():


def get_segments_including_custom_replacements(phase, user_input, reserved_entities_dict, ner_entities, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, anonymise_title_cased_word_sequences, anonymise_urls, anonymise_emails, anonymise_phone_numbers, ner_model):

  for segment in get_segments_from_ner(phase, user_input, reserved_entities_dict, ner_entities, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, ner_model):

    text_original = segment["text"]
    label = segment["label"]
    ner_segment_start_char = segment["start_char"]
    ner_segment_end_char = segment["end_char"]
    replacement = segment["replacement"]
    text_normalised =  segment["text_normalised"]


    if replacement is not None or text_normalised is not None:    # if replacement is None and text_normalised is not None then it means the segment was recognised as an independent entity, but was treated as not anonymisable entity. So no need to recheck it here using regexes.

      yield segment

    else:

      regexes = []
      pattern_types = []
        
          
      if anonymise_emails:
        regexes.append(email_re)
        pattern_types.append("Email")
        regexes.append(at_gmail_re)
        pattern_types.append("Email")
          

      if anonymise_urls:  
        regexes.append(http_re)
        pattern_types.append("Url")
        regexes.append(url_like_re)
        pattern_types.append("Url")
        regexes.append(www_re)
        pattern_types.append("Url")
        regexes.append(domain_re)
        pattern_types.append("Url")


      if anonymise_numbers:
        regexes.append(number_without_spaces_with_dot_or_comma_re)
        pattern_types.append("Number")

      if anonymise_phone_numbers: 
        regexes.append(phone_without_dots_re)
        if anonymise_numbers:
          pattern_types.append("Number or Phone")
        else:
          pattern_types.append("Phone")
  
      if anonymise_phone_numbers: 
        regexes.append(phone_with_dots_re)
        if anonymise_numbers:
          pattern_types.append("Number or Phone")
        else:
          pattern_types.append("Phone")
        
      if anonymise_numbers:
        regexes.append(number_without_spaces_without_dot_or_comma_re)
        pattern_types.append("Number")

      if anonymise_numbers:   # numbers with spaces are detected only after phone number pattern
        regexes.append(number_with_spaces_re)
        pattern_types.append("Number")

      if anonymise_title_cased_word_sequences:
        regexes.append(title_cased_words_re)
        pattern_types.append("Name or Title")

      
      # TODO:
      # Usernames
      # use percent_dollar_eur_pound_re ?


      prev_ent_end = ner_segment_start_char

      if len(regexes) > 0:

        combined_regexes = ["(" + (x.pattern if isinstance(x, regex.Pattern) else x) + ")" for x in regexes]

        combined_regex = "(" + "|".join(combined_regexes) + ")"
        combined_regex = regex.compile(combined_regex)
        re_matches = combined_regex.finditer(" " + text_original + " ")   # NB! adding spaces since the regex requires a space, bracket, or punctuation before the start and after the end of a match

        for re_match in re_matches:

          re_text_original = re_match.group(1)
          # re_start_char = re_match.start(1) - 1 + ner_segment_start_char   # NB! -1 since the text was prepended with a space
          # re_end_char = re_match.end(1) - 1 + ner_segment_start_char   # NB! -1 since the text was prepended with a space


          # re_text_normalised = regex.sub(r"\s+", " ", re_text_original) # normalise the dictionary keys so that same entity with different space formats gets same replacement

          #if phase == 0 and re_text_normalised in reserved_entities_dict: # Regex may detect texts like "Location C" as entities when title cased words detection is turned on
          #  continue


          type = None
          # detect the pattern type
          for i in range(0, len(pattern_types)):
            re_match2 = regex.search(regexes[i], " " + re_text_original + " ")   
            if re_match2 is not None:   # NB! adding spaces since the regex requires a space, bracket, or punctuation before the start and after the end of a match
              type = pattern_types[i]
              if type == "Number" and not anonymise_numbers:
                type = None   # do not replace this text segment

              if type is not None:
                # NB! consider re_match2 in order to not include lookaheads in the re_text_original2. combined_regex will include lookaheads since it is inside ()
                re_text_original2 = re_match2.group(0)
                re_start_char = re_match.start(1) - 1 + re_match2.start(0) - 1 + ner_segment_start_char   # NB! -1 since the text was prepended with a space
                re_end_char = re_match.start(1) - 1 + re_match2.end(0) - 1 + ner_segment_start_char   # NB! -1 since the text was prepended with a space

                re_text_normalised2 = regex.sub(r"\s+", " ", re_text_original2) # normalise the dictionary keys so that same entity with different space formats gets same replacement
                if phase == 0 and re_text_normalised2 in reserved_entities_dict: # Regex may detect texts like "Location C" as entities when title cased words detection is turned on
                  type = None

                if type == "Number or Phone" and anonymise_numbers and len(re_text_original2) <= 5:   # if number detection is turned on then treat short numbers rather as numbers, not as phone   # TODO: config parameter for the threshold value
                  type = "Number"

              break

          if type is not None:
            replacement = type
          else:
            continue

          if prev_ent_end < re_start_char:
            yield {
              "text": user_input[prev_ent_end:re_start_char],
              "label": None,
              "start_char": prev_ent_end,
              "end_char": re_start_char,
              "replacement": None,
              "text_normalised": None,
            }

          yield {
            "text": re_text_original2,
            "label": label,
            "start_char": re_start_char,
            "end_char": re_end_char,
            "replacement": replacement,
            "text_normalised": re_text_normalised2,
          } 

          prev_ent_end = re_end_char

        #/ for match in matches:

      #/ if len(regexes) > 0:

      if prev_ent_end < ner_segment_end_char:
        yield {
          "text": user_input[prev_ent_end:ner_segment_end_char],
          "label": None,
          "start_char": prev_ent_end,
          "end_char": ner_segment_end_char,
          "replacement": None,
          "text_normalised": None,
        }

    #/ if replacement is not None: 

  #/ for segment in get_segments_from_ner():

#/ def get_segments_including_custom_replacements():


class DummyNer:   # for debugging
  def __init__(self, user_input):
    self.ents = []


def anonymise(user_input, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, anonymise_title_cased_word_sequences, anonymise_urls, anonymise_emails, anonymise_phone_numbers, ner_model, use_only_numeric_replacements = False, state = None):
  global spacy_loaded #, spacy

  # TODO!!! speed up the process by detecting cells with same content as before and applying same result
  # TODO!!! speed up the process by skipping empty cells

  if True:    # for debugging regex-based entities
    # if not spacy_loaded:
    with Timer("Loading Spacy", quiet=spacy_loaded):
      import spacy    # load it only when anonymisation is requested, since this package loads slowly
      spacy.prefer_gpu()
      spacy_loaded = True

    NER = ner_cache.get(ner_model)
    if NER is None:
      with Timer(f"Loading Named Entity Recognition model {ner_model}"):
        NER = spacy.load(ner_model)
        ner_cache[ner_model] = NER


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
    #
    #Em Dash (—)
    #Unicode: U+2014
    #Description: Much longer than an en dash or hyphen. It's generally used for breaks in thought or longer pauses in sentences, not typically in names, but there are exceptions in certain artistic or stylized uses.

    #Figure Dash (‒)
    #Unicode: U+2012
    #Description: Similar in width to a hyphen. It's used primarily in numerical contexts, like phone numbers, rather than in names.

    #Horizontal Bar (―)
    #Unicode: U+2015
    #Description: A dash character that is sometimes used like an em dash. It is also used in bibliographies and certain types of formal names but is relatively rare.

    # lets accept all sorts of dashes after words since the next word might be not a name anymore
    dash_between_words_re = r'[\u002D\u2011\u2013\u2014\u2012\u2015]'

    # add spaces after words in case "(" or "- " character follows a lower case letter. Exclude "word(s)" sequence in case of brackets. Else NER will not process these words. TODO: if lower case letter follows upper cased word, then should we handle that as well?
    # TODO: preserve "someword(s)" sequence only in English text
    # TODO: restore original character locations later

    bracket_or_dash_re = r'(\p{Ll})((?!\(s\))[' + left_brac + r']|' + dash_between_words_re + r'\s|[\/\\]\s?)'   # include / and \ chars here as well but do not require space after it
    user_input = regex.sub(bracket_or_dash_re, r'\1 \2', user_input)


    with Timer("Running NER", quiet=True):
      try:
        ner_entities = NER(user_input)
      except ValueError as ex:  # for some content, NER fails with message like "ValueError: Shape mismatch for blis.gemm: (1, 0), (768, 49)"
        result = "NER error"    # TODO: make the error message configurable
        return result, state

  else:
    ner_entities = DummyNer(user_input)


  result = ""

  if state is None:
    letters = string.ascii_uppercase if not use_only_numeric_replacements else ""
    next_available_replacement_letter_index = 0
    entities_dict = {}
    reserved_replacement_letter_indexes = set()

    # exclude I letter from this list since it is confusing
    replacement_letter_index = ord("I") - ord("A")
    reserved_replacement_letter_indexes.add(replacement_letter_index)

  else:   #/ if state is None:
    letters = state["letters"]
    next_available_replacement_letter_index = state["next_available_replacement_letter_index"]
    entities_dict = state["entities_dict"]
    reserved_replacement_letter_indexes = state["reserved_replacement_letter_indexes"]


  # TODO: Russian translations of the replacements
  active_replacements = ""
  if anonymise_names:
    active_replacements += "Person|Group|Building|Organisation|Area|Location|Event|Language"

  if active_replacements != "" and anonymise_numbers:
    active_replacements += "|"
  if anonymise_numbers:
    active_replacements += "Money Amount|Quantity|Number"

  if active_replacements != "" and anonymise_dates:
    active_replacements += "|"
  if anonymise_dates:
    active_replacements += "Calendar Date or Age|Calendar Date|Age"   # TODO: add numeric date and textual date?

  if active_replacements != "" and anonymise_titles_of_work:
    active_replacements += "|"
  if anonymise_titles_of_work:
    active_replacements += "Title of Work" 

  if active_replacements != "" and anonymise_emails:
    active_replacements += "|"
  if anonymise_emails:
    active_replacements += "Email"

  if active_replacements != "" and anonymise_urls:
    active_replacements += "|"
  if anonymise_urls:
    active_replacements += "Url"

  if active_replacements != "" and anonymise_phone_numbers:
    active_replacements += "|"
  if anonymise_phone_numbers and anonymise_numbers:
    active_replacements += "Number or Phone"
  elif anonymise_phone_numbers and not anonymise_numbers:
    active_replacements += "Phone"

  if active_replacements != "" and anonymise_title_cased_word_sequences:
    active_replacements += "|"
  if anonymise_title_cased_word_sequences:
    active_replacements += "Name or Title"


  reserved_entities_dict = {}

  if len(active_replacements) > 0:

    # detect any pre-existing anonymous entities like Person A, Person B in the input text and reserve these letters in the dict so that they are not reused

    with Timer("Running regexes", quiet=True):
      re_matches = regex.findall(r"(^|\s)(" + active_replacements + r")(\s+)([" + regex.escape(letters) + r"]|[0-9]+)(\s|:|$)", user_input) # NB! capture also numbers starting with 0 so that for example number 09 still ends up reserving number 9.

    for re_match in re_matches:

      replacement = re_match[1]
      space = re_match[2]
      letter = re_match[3]

      if letter.isalpha():    # alphabetical replacement indexes
        replacement_letter_index = ord(letter) - ord("A") 
        reserved_replacement_letter_indexes.add(replacement_letter_index)

      else:   # numeric replacement indexes
        intval = int(letter)
        if intval == 0:    # this algorithm does not produce replacement number 0, so we do not need to reserve it, also reserving it would result it reserving last letter from alphabet instead
          continue

        replacement_letter_index = len(letters) + intval - 1   # NB! -1 since replacement numbers start from 1 in the line "replacement_letter = str(replacement_letter_index + 1)"
        reserved_replacement_letter_indexes.add(replacement_letter_index)

      reserved_entities_dict[replacement + " " + letter] = replacement_letter_index

      # NB! save to entities_dict as well so that this phrase is reserved for all sheet cells
      # TODO!!! need to process all sheet cells for reserved phrases before starting NER
      # entities_dict[replacement + " " + letter] = replacement_letter_index  # use space as separator to normalise the dictionary keys so that same entity with different space formats gets same replacement
      
    #/ for re_match in re_matches:

  #/ if len(active_replacements) > 0:



  for phase in range(0, 2): # Two phases: 1) counting unique entities, 2) replacing them. Phase 1 is needed so that same entity will have same replacement in all places.
    for segment in get_segments_including_custom_replacements(phase, user_input, reserved_entities_dict, ner_entities, anonymise_names, anonymise_numbers, anonymise_dates, anonymise_titles_of_work, anonymise_title_cased_word_sequences, anonymise_urls, anonymise_emails, anonymise_phone_numbers, ner_model):

      text_original = segment["text"]
      replacement = segment["replacement"]
      text_normalised = segment["text_normalised"]


      if replacement is None:

        if phase == 1:
          result += text_original 

      else:

        if phase == 0:

          if text_normalised not in entities_dict:

            while next_available_replacement_letter_index in reserved_replacement_letter_indexes:
              next_available_replacement_letter_index += 1

            replacement_letter_index = next_available_replacement_letter_index

            entities_dict[text_normalised] = replacement_letter_index
            reserved_replacement_letter_indexes.add(replacement_letter_index)

          #/ if text_normalised not in entities_dict:

        else:   #/ if phase == 0:

          replacement_letter_index = entities_dict[text_normalised]

          if len(reserved_replacement_letter_indexes) <= len(letters):
            replacement_letter = letters[replacement_letter_index]
          else:
            replacement_letter = str(replacement_letter_index + 1)  # use numeric names if there are too many entities in input to use letters

          result += replacement + " " + replacement_letter

        #/ if phase == 0:

      #/ if replacement is None:

    #/ for segment in get_segments_including_custom_replacements():
  #/ for phase in range(0, 2):


  state = {
    "letters": letters,
    "next_available_replacement_letter_index": next_available_replacement_letter_index,
    "entities_dict": entities_dict,
    "reserved_replacement_letter_indexes": reserved_replacement_letter_indexes,
  }

  return result, state

#/ def anonymise_uncached()



