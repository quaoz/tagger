#!/usr/bin/env python3

import datetime
import os
import re
import time
import argparse

import pylast
from dotenv import load_dotenv
from rymscraper.rymscraper import rymscraper


def get_tags(album_item: pylast.Album, clean_name: bool) -> list[str]:
	message(album_item, i, album_count, clean_name=clean_name)
	album_title = clean_album_title(album_item.title) if clean_name else album_item.title

	# Retrieve the album from RYM
	rym_album = rym_network.get_album_infos(name=f"{album_item.artist} - {album_title}")

	# Extract and process the genres and descriptors
	genres = clean_tags(re.split(r'\n|,', rym_album.get("Genres")))
	if PRINT_TAGS and not SILENT:
		print(f"Genres:      {genres}")

	if USE_DESCRIPTORS:
		descriptors = clean_tags(re.split(r'\n|,', rym_album.get("Descriptors")))
		if PRINT_TAGS and not SILENT:
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
	if SILENT:
		return

	max_length = 170
	bar_length = 50

	album_title = clean_album_title(album_item.title) if clean_name else album_item.title

	# Fancy progress bar stuff
	filled_len = int(round(bar_length * index / float(total)))
	percents = round(100.0 * index / float(total), 1)
	bar = "█" * filled_len + "-" * (bar_length - filled_len)

	justify = " " * ((max_length - bar_length) - (
				len(album_title) + len(str(album_item.artist)) + len(prefix) + len(suffix)))
	print("%s%s by %s %s%s [%s] %s%s  %s/%s  ETA: %s" % (
	prefix, album_title, album_item.artist, suffix, justify, bar, percents, '%', index, total,
	str(datetime.timedelta(seconds=(((time.time() - start) / (index + 1)) * (total - index))))))


def clean_album_title(title: str) -> str:
	for common_term in ["original", "version", "remastered", "mixtape", "deluxe", "edition", "extended", "the remaster",
						"remaster", "expanded", "bonus track", "complete", "live", "single", "ep", "-", "&"]:
		title = title.lower().replace(common_term, "")

	# Removes text within brackets
	return re.sub("[(\\[].*?[)\\]]", "", title).strip()


def clean_tags(items: list[str]) -> list[str]:
	tags = []

	# Removes all unsupported characters for lastfm tags (keeps alphanumeric characters, space and dash)
	for item in items:
		tags.append(re.sub(r"[^0-9A-Za-z -]+", "", item.replace("&", "n")).strip())

	return tags


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Tag last.fm albums with RYM genres and descriptors")

	parser.add_argument("--keep", action="store_true", help="keep existing last.fm tags")
	parser.add_argument("--no-descriptors", action="store_true", help="don't use RYM descriptors as tags")
	parser.add_argument("--no-auto-tag", action="store_true", help="don't add the auto-tagged tag")
	parser.add_argument("--no-auto-skip", action="store_true", help="don't skip albums with the auto-tagged tag")
	parser.add_argument("--week", action="store_true", help="only tag albums from the past week")
	parser.add_argument("--print", action="store_true", help="print the tags")
	parser.add_argument("--silent", action="store_true", help="silences the script")
	parser.add_argument("--dry", action="store_true", help="stops tags from being submitted to last.fm")

	parser.add_argument("--limit", required=False, type=int, default=1000,
						help="number of albums to tag, unused when --week is used")
	parser.add_argument("--skip", required=False, type=int, default=0,
						help="skips a given number of albums, useful if the script stopped")

	parser.add_argument("--key", metavar="API_KEY", required=False, type=str,
						help="last.fm api key, can be specified in the .env file")
	parser.add_argument("--secret", metavar="API_SECRET", required=False, type=str,
						help="last.fm api secret, can be specified in the .env file")
	parser.add_argument("--username", metavar="USERNAME", required=False, type=str,
						help="last.fm username, can be specified in the .env file")
	parser.add_argument("--password", metavar="HASH", required=False, type=str,
						help="last.fm password md5 hash can be found using the --hash argument, can be specified in the .env file")
	parser.add_argument("--hash", metavar="PASSWORD", required=False, type=str, help="last.fm password to hash")

	parser.format_help()
	args = parser.parse_args()

	if args.hash is not None:
		print(f"Password hash: {pylast.md5(args.hash)}")
		exit(0)

	# Whether existing last.fm tags should be removed or not
	REMOVE_TAGS = not args.keep

	# Whether RYM descriptors should be used as tags, disable if unsure what descriptors are
	USE_DESCRIPTORS = not args.no_descriptors

	# Whether to add the auto-tagged tag (needed to skip already tagged albums, see SKIP_AUTO_TAGGED)
	AUTO_TAGGED_TAG = not args.no_auto_tag

	# Whether to skip albums with the auto-tagged tag
	SKIP_AUTO_TAGGED = not args.no_auto_skip

	# Whether to only tag albums from the past week
	TAG_THIS_WEEK = args.week

	# The number of albums to tag, ignored if tagging this week's albums (TAG_THIS_WEEK = True), set to the number of
	# albums scrobbled to try and tag every album
	ALBUM_LIMIT = args.limit

	# Lets you skip a given number of albums, useful if the script was stopped after a number of albums as it allows you
	# to continue from that point
	SKIP_INDEX = args.skip

	# Whether to print the genres and descriptors from RYM
	PRINT_TAGS = args.print

	# Whether to silence the script
	SILENT = args.silent

	# Whether it should actually write the tags or just display them, if True no tags will be changed
	DRY_RUN = args.dry

	# Reads in the lastfm credentials
	load_dotenv()
	API_KEY = args.key if args.key is not None else os.getenv("API_KEY")
	API_SECRET = args.secret if args.secret is not None else os.getenv("API_SECRET")
	USERNAME = args.username if args.username is not None else os.getenv("USERNAME")
	PASSWORD_HASH = args.hash if args.hash is not None else os.getenv("PASSWORD_HASH")

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

	if not SILENT:
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
				message(
					album_item=album.item, index=i, total=album_count, prefix="Skipping: ", suffix="- already tagged")
			else:
				found = True
				try:
					album_tags = get_tags(album.item, False)
				except (IndexError, AttributeError, TypeError) as e:
					if not SILENT:
						print(
							f"Unable to find {album.item.title} by {album.item.artist} on RYM - trying to sanitize the album title...")
					try:
						album_tags = get_tags(album.item, True)
					except (IndexError, AttributeError, TypeError) as e:
						if not SILENT:
							print(f"Unable to find {clean_album_title(album.item.title)} by {album.item.artist} on RYM")
						found = False

				if found:
					tag_album(album.item, album_tags)
				time.sleep(2.5)

	rym_network.browser.close()
	rym_network.browser.quit()
