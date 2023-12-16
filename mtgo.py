import requests
import json
import os
import re
import datetime
from datetime import datetime

CACHE_DIR = "./cache"
DEBUG = True
CARDS = {}

def extract_events_from_month(month, year):
	return extract_events_from_month_url(build_month_url(month, year))

def extract_events_from_month_url(month_url):
	if DEBUG:
		print("[-] " + month_url )
	month_file = month_url.split("/")[-1] + "_" + month_url.split("/")[-2]

	if check_cached(month_file):
		body = load_cache(month_file)
	else:
		if DEBUG:
			print("[-] Downloading month data:" + month_url.split("/")[-1] + " " +  month_url.split("/")[-2])
		r = requests.get(month_url)
		body = r.text
		save_data(month_file, body)
	return re.findall("/en/mtgo/decklist/([\w\-]+)", body)

def check_cached(file_name):
	if os.path.exists(CACHE_DIR + "/" + file_name):
		print("[-] File already in cache: " + file_name)
		return True
	return False

def extract_event_name_from_event_url(event_url):
	return str(event_url.split("/")[-1])

def load_cache(file_name):
	return open(CACHE_DIR + "/" + file_name).read()
	
def save_data(file_name, data):
	if DEBUG:
		print("[-] Saving data in local cache ");
	f = open(CACHE_DIR + "/" + file_name, "w+")
	f.write(data)
	f.close()

def delete_cache(file_name):
	os.unlink(CACHE_DIR + "/" + file_name)

def fetch_event_data_from_event_name(event_name):
	event_url = "https://www.mtgo.com/en/mtgo/decklist/" + event_name
	return fetch_event_data_from_event_url(event_url) 

def fetch_event_data_from_event_url(event_url):
	event_name = extract_event_name_from_event_url(event_url)
	if check_cached(event_name):
		body = load_cache(event_name)
	else:
		if DEBUG:
			print("[-] Downloading data from event: " + event_name )
		r = requests.get(event_url)
		body = r.text
		save_data(event_name, body)

	if check_cached(event_name + ".json"):
		event_data = load_cache(event_name + ".json")
	else:
		event_data = body.split("window.MTGO.decklists.data = ")[1].split(";")[0]
		save_data(event_name + ".json", event_data) 
	return json.loads(event_data)

def extract_cards_from_event_data(event_data):
	cards = {}
	for deck_id in event_data['decks']:
		my_range = len(deck_id['deck'])
		for i in range(my_range):
			for card_id in deck_id['deck'][i]['DECK_CARDS']:
				card_quantity = int(card_id['Quantity'])
				card_name = str(card_id['CARD_ATTRIBUTES']['NAME'])
				card_rarity = str(card_id['CARD_ATTRIBUTES']['RARITY'])

				#print("Card Name: " + card_name + " " + str(card_quantity))

				if card_name in cards.keys():
					#cards[card_name]['quantity'] += card_quantity
					cards[card_name]['quantity'] += 1
				else:
					cards[card_name] = {}
					cards[card_name]['quantity'] = card_quantity
					cards[card_name]['rarity'] = card_rarity

				#print("Card Name: " + card_name + " " + str(cards[card_name]))
	return cards

def build_month_url(month, year):
	return "https://www.mtgo.com/en/mtgo/decklists/" + str(year) + "/" + str(month) 

def collect_year(year, format):
	for month in range(1,12):

		current_month = datetime.now().month
		current_year = datetime.now().year
	
		if int(year) < 2015:
			break
		
		if int(year) == 2015 and month < 11:
			continue
	
		if int(year) == current_year:

			if month == current_month:
				try:
					delete_cache(str("%02d" % month) + "_" + str(year))
				except:
					print("No yet downloaded")

			if month == current_month + 1:
				print("No further data available")
				return

		month = "%02d" % month
		events = extract_events_from_month_url(build_month_url(month, year))
		for event_name in events:
			if format in event_name:
				event_data = fetch_event_data_from_event_name(event_name)
				if DEBUG:
					print("[-] Adding data from event" + event_name)
					merge_cards(extract_cards_from_event_data(event_data))

def merge_cards(cards):
	for card_name, card_proprieties in cards.items():

		card_quantity = card_proprieties['quantity']
		card_rarity = card_proprieties['rarity']

		if card_name in CARDS.keys():
			# CARDS[card_name] += card_quantity
			CARDS[card_name]['quantity'] += 1
		else:
			CARDS[card_name] = {}
			CARDS[card_name]['quantity'] = card_quantity
			CARDS[card_name]['rarity'] = card_rarity

import sys

years = (2015,2016,2017,2018,2019,2020,2021,2022,2023)

if len(sys.argv) >= 3:
	format = sys.argv[2]
else:
	format = 'vintage'

if len(sys.argv) >= 2:
	year = sys.argv[1]
	collect_year(year, format)
else:
	for year in years:
		collect_year(year, format)

for c, p in CARDS.items():
	r = p['rarity']
	q = p['quantity']
	print(q,c,r)
