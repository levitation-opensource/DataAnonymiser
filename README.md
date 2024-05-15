# DataAnonymiser

This software anonymises data inside text files and CSV-like files. It removes various sorts of personally identifiable information. Each removed part is replaced with a suitable generic text, depending on the type of removed data. Currently English and Russian languages are supported. Russian works both with Cyrillic and Latin characters.


## Example input and output files

<a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/test_input_en.txt"><u>data/test_input_en.txt</u></a> - <a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/example_output_en.txt"><u>data/example_output_en.txt</u></a>

<a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/test_input_en.csv"><u>data/test_input_en.csv</u></a> - <a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/example_output_en.csv"><u>data/example_output_en.csv</u></a>

<a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/test_input_ru_cyr.txt"><u>data/test_input_ru_cyr.txt</u></a> - <a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/example_output_ru_cyr.txt"><u>data/example_output_ru_cyr.txt</u></a>

<a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/test_input_ru_lat.txt"><u>data/test_input_ru_lat.txt</u></a> - <a href="https://github.com/levitation-opensource/DataAnonymiser/blob/main/data/example_output_ru_lat.txt"><u>data/example_output_ru_lat.txt</u></a>


## How it works

This software uses a combination of Named Entity Recognition (NER) and regular expressions to perform its function.


## Usage

`python Recogniser.py "input_file.txt"|"input_file.csv"|"input_file.tsv" ["output_file.txt"|"output_file.csv"|"output_file.tsv"]`

The user provided files are expected to be in the same folder as the main Python script, unless an absolute path is provided. If run without arguments then sample files in the `data` folder are used. If the user provides input file name but no output file name then the output file name will be calculated as `input filename` + `_anonymised` + `.input filename extension`.


## Current project state
Ready to use. Is actively developed further.
