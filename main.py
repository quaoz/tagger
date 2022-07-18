import os
import re
import time

import pylast
from dotenv import load_dotenv
from rymscraper import rymscraper


def clean(items):
	tags = []

	# Removes all unsupported characters for lastfm tags (keeps alphanumeric characters, space and dash)
	for item in items:
		tags.append(re.sub(r"[^0-9A-Za-z -]+", '', item.replace("&", "n")).strip())

	return tags


if __name__ == '__main__':
	# Whether existing tags should be removed or not
	REMOVE_TAGS = True

	# Whether RYM descriptors should be used as tags
	USE_DESCRIPTORS = True

	# Whether to add the auto-tagged tag (needed to skip already tagged albums, see SKIP_AUTO_TAGGED)
	AUTO_TAGGED_TAG = True

	# Whether to skip albums with the auto-tagged tag
	SKIP_AUTO_TAGGED = True

	# Whether to only tag albums from the past week
	TAG_THIS_WEEK = False

	# The number of albums to tag, ignored if tagging this week's albums (TAG_THIS_WEEK = True), set to the number of
	# albums scrobbled to try and tag every album
	ALBUM_LIMIT = 900

	# Lets you skip a given number of albums, useful if the script was stopped after a number of albums as it allows you
	# to continue from that point
	SKIP_INDEX = 0

	# Whether it should actually write the tags or just display them, if True no tags will be changed
	DRY_RUN = False

	# Reads in the lastfm credentials
	load_dotenv()
	API_KEY = os.getenv("API_KEY")
	API_SECRET = os.getenv("API_SECRET")
	USERNAME = os.getenv("USERNAME")
	PASSWORD_HASH = os.getenv("PASSWORD_HASH")

	# Create lastfm network
	lastfm_network = pylast.LastFMNetwork(
		api_key=API_KEY,
		api_secret=API_SECRET,
		username=USERNAME,
		password_hash=PASSWORD_HASH,
	)

	# Create RYM network
	rym_network = rymscraper.RymNetwork()

	# Get the user
	user = lastfm_network.get_authenticated_user()

	if TAG_THIS_WEEK:
		albums = user.get_weekly_album_charts(user.get_weekly_chart_dates()[0])
	else:
		albums = user.get_top_albums(limit=ALBUM_LIMIT)

	print(
		f"CONFIG: REMOVE_TAGS: {REMOVE_TAGS}, USE_DESCRIPTORS: {USE_DESCRIPTORS}, AUTO_TAGGED_TAG: {AUTO_TAGGED_TAG}, "
		f"SKIP_AUTO_TAGGED: {SKIP_AUTO_TAGGED}, TAG_THIS_WEEK: {TAG_THIS_WEEK}, ALBUM_LIMIT: {ALBUM_LIMIT}, SKIP_INDEX:"
		f" {SKIP_INDEX}, DRY_RUN: {DRY_RUN}, user: {lastfm_network.get_authenticated_user().name}"
	)

	index = 1

	for album in albums:
		if index >= SKIP_INDEX:
			already_tagged = False

			# Skips albums with the auto-tagged tag
			if SKIP_AUTO_TAGGED:
				for tag in album.item.get_tags():
					if "auto-tagged" in tag.name:
						already_tagged = True
						break

			if already_tagged:
				print(f"Skipping: {album.item.title} by {album.item.artist} ({index}) - already tagged\n")
			else:
				try:
					print(f"{album.item.title} by {album.item.artist} ({index}):")

					# Retrieve the album from RYM
					rym_album = rym_network.get_album_infos(name=f"{album.item.artist} - {album.item.title}")

					# Extract and process the genres and descriptors
					genres = clean(rym_album.get("Genres").replace("\n", ", ").split(", "))
					print(f"Genres:      {genres}")

					descriptors = clean(
						rym_album.get("Descriptors").replace("\n", ", ").split(", ")) if USE_DESCRIPTORS else None
					print(f"Descriptors: {descriptors}\n")

					# Add the tags
					if not DRY_RUN:
						if REMOVE_TAGS:
							album.item.remove_tags(tags=album.item.get_tags())

						if USE_DESCRIPTORS:
							album.item.add_tags(tags=descriptors)

						if AUTO_TAGGED_TAG:
							album.item.add_tag("auto-tagged")

						album.item.add_tags(tags=genres)

				except (IndexError, AttributeError, TypeError) as e:
					print(f"Unable to find {album.item.title} by {album.item.artist} ({index}) on RYM\n")
				time.sleep(2.5)
		index += 1
