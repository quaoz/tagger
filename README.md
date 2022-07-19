# Tagger

A script to tag scrobbled albums on [last.fm](https://last.fm) with genres (and optionally descriptors) from [Rate Your Music](https://rateyourmusic.com). The script is slow mainly due to the long time taken to retrieve tags from RYM, to tag 1000 albums took me around 6 hours. Excessive scraping of RYM may result in you being IP banned for a few days however this is not a problem I have run into.

## Installation

```shell
# Clone this repository
git clone https://github.com/quaoz/tagger.git
cd tagger

# Rename example.env to .env and fill in your details
cp example.env .env
nano .env

# Clone rymscraper
git clone https://github.com/dbeley/rymscraper.git

# Create the pipenv and install the requirements
pipenv shell
pipenv install -e rymscraper
pipenv install -r requirements.txt

# Check that the options defined in the script suite you. At the very least you will need to change DRY_RUN to False for the script to do anything but you should read through all the options.
# The options begin after line 98 (if __name__ == '__main__':)
nano main.py

# Run the script
python main.py
```
