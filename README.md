# Tagger

A script to tag scrobbled albums on [last.fm](https://last.fm) with genres (and optionally descriptors) from [Rate Your Music](https://rateyourmusic.com). The script is slow mainly due to the long time taken to retrieve tags from RYM, to tag 1000 albums took me around 6 hours. Excessive scraping of RYM may result in you being IP banned for a few days however this is not a problem I have run into.

## Installation

```shell
# Clone this repository
git clone https://github.com/quaoz/tagger.git
cd tagger

# Rename example.env to .env and fill in your details
cp example.env .env
nvim .env

# Clone rymscraper
git clone https://github.com/dbeley/rymscraper.git

# Install the requirements with pipenv
pipenv install -e rymscraper
pipenv install -r requirements.txt

# Or install with pip if you do not want to use pipenv, if installed 
# without pienv you can just use "python3 main.py" to run the script
python3 rymscraper/setup.py install
pip3 install -r requirements.txt
```

## Usage

```
$ pipenv run python3 main.py --help

usage: main.py [-h] [--keep] [--no-descriptors] [--no-auto-tag] [--no-auto-skip] [--week] 
      [--print] [--silent] [--dry] [--limit LIMIT] [--skip SKIP] [--key API_KEY] 
      [--secret API_SECRET] [--username USERNAME] [--password HASH] [--hash PASSWORD]

Tag last.fm albums with RYM genres

optional arguments:
  -h, --help           show this help message and exit
  --keep               keep existing last.fm tags
  --no-descriptors     don't use RYM descriptors as tags
  --no-auto-tag        don't add the auto-tagged tag
  --no-auto-skip       don't skip albums with the auto-tagged tag
  --week               only tag albums from the past week
  --print              print the tags
  --silent             silences the script
  --dry                stops tags from being submitted to last.fm
  --limit LIMIT        number of albums to tag, unused when --week is used
  --skip SKIP          skips a given number of albums, useful if the script stopped
  --key API_KEY        last.fm api key, can be specified in the .env file
  --secret API_SECRET  last.fm api secret, can be specified in the .env file
  --username USERNAME  last.fm username, can be specified in the .env file
  --password HASH      last.fm password md5 hash can be found using the --hash argument, 
                       can be specified in the .env file
  --hash PASSWORD      last.fm password to hash
```
