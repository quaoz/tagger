import datetime
import os
import re
import time

import pylast
from dotenv import load_dotenv
from rymscraper import rymscraper


def get_tags(album_item: pylast.Album, clean_name: bool) -> list[str]:
	message(album_item, i, album_count, clean_name=clean_name)
	album_title = clean_album_title(album_item.title) if clean_name else album_item.title

	# Retrieve the album from RYM
	rym_album = rym_network.get_album_infos(name=f"{album_item.artist} - {album_title}")

	# Extract and process the genres and descriptors
	genres = clean_tags(rym_album.get("Genres").replace("\n", ", ").split(", "))
	if PRINT_TAGS:
		print(f"Genres:      {genres}")

	if USE_DESCRIPTORS:
		descriptors = clean_tags(rym_album.get("Descriptors").replace("\n", ", ").split(", "))
		if PRINT_TAGS:
			print(f"Descriptors: {descriptors}")
		genres = genres + descriptors

	return genres


def tag_album(album_item: pylast.Album, tags: list[str]):
	# Add the tags
	if not DRY_RUN:
		if REMOVE_TAGS:
			album_item.remove_tags(tags=album_item.get_tags())

		if AUTO_TAGGED_TAG:
			album_item.add_tag("auto-tagged")

		album_item.add_tags(tags=tags)


def get_albums() -> list[pylast.TopItem]:
	if TAG_THIS_WEEK:
		return user.get_weekly_album_charts(user.get_weekly_chart_dates()[0])
	else:
		return user.get_top_albums(limit=ALBUM_LIMIT)


def already_tagged(album_item: pylast.Album) -> bool:
	# Skips albums with the auto-tagged tag
	if SKIP_AUTO_TAGGED:
		for tag in album_item.get_tags():
			if "auto-tagged" in tag.name:
				return True

	return False


def message(album_item: pylast.Album, index: int, total: int, prefix="", suffix="", clean_name=False):
	max_length = 160
	bar_length = 60

	album_title = clean_album_title(album_item.title) if clean_name else album_item.title

	# Fancy progress bar stuff
	filled_len = int(round(bar_length * index / float(total)))
	percents = round(100.0 * index / float(total), 1)
	bar = "█" * filled_len + "-" * (bar_length - filled_len)

	justify = " " * ((max_length - bar_length) - (
			len(album_title) + len(str(album_item.artist)) + len(prefix) + len(suffix)))
	print("%s%s by %s %s%s [%s] %s%s  %s/%s  ETA: %s" % (prefix, album_title, album_item.artist, suffix, justify, bar,
														 percents, '%', index, total, str(datetime.timedelta(
		seconds=(((time.time() - start) / (index + 1)) * (total - index))))))


def clean_album_title(title: str) -> str:
	for common_term in ["original", "version", "remastered", "mixtape", "deluxe", "edition", "extended", "the remaster",
						"remaster", "expanded", "bonus track", "complete"]:
		title = title.lower().replace(common_term, "")

	# Removes text within brackets
	return re.sub("\\(.*?\\)", "", title).strip()


def clean_tags(items: list[str]) -> list[str]:
	tags = []

	# Removes all unsupported characters for lastfm tags (keeps alphanumeric characters, space and dash)
	for item in items:
		tags.append(re.sub(r"[^0-9A-Za-z -]+", "", item.replace("&", "n")).strip())

	return tags


if __name__ == '__main__':
	# Whether existing tags should be removed or not
	REMOVE_TAGS = True

	# Whether RYM descriptors should be used as tags, disable if unsure what descriptors are
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

	# Whether to print the genres and descriptors from RYM
	PRINT_TAGS = True

	# Whether it should actually write the tags or just display them, if True no tags will be changed
	DRY_RUN = True

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

	albums = get_albums()
	album_count = len(albums)

	print(
		f"CONFIG: REMOVE_TAGS: {REMOVE_TAGS}, USE_DESCRIPTORS: {USE_DESCRIPTORS}, AUTO_TAGGED_TAG: {AUTO_TAGGED_TAG}, "
		f"SKIP_AUTO_TAGGED: {SKIP_AUTO_TAGGED}, TAG_THIS_WEEK: {TAG_THIS_WEEK}, ALBUM_LIMIT: {ALBUM_LIMIT}, SKIP_INDEX:"
		f" {SKIP_INDEX}, DRY_RUN: {DRY_RUN}, album_count: {album_count}, user: "
		f"{lastfm_network.get_authenticated_user().name}\n"
	)

	start = time.time()

	for i, album in enumerate(albums):
		if i + 1 >= SKIP_INDEX:
			if already_tagged(album.item):
				message(album_item=album.item, index=i, total=album_count, prefix="Skipping: ", suffix="- already tagged")
			else:
				found = True
				try:
					album_tags = get_tags(album.item, False)
				except (IndexError, AttributeError, TypeError) as e:
					print(
						f"Unable to find {album.item.title} by {album.item.artist} on RYM - trying to sanitize the album title...")
					try:
						album_tags = get_tags(album.item, True)
					except (IndexError, AttributeError, TypeError) as e:
						print(f"Unable to find {clean_album_title(album.item.title)} by {album.item.artist} on RYM")
						found = False

				if found:
					tag_album(album.item, album_tags)
				time.sleep(2.5)
