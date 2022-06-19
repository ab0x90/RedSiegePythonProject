#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import argparse
import sys
import collections
from string import punctuation
from urllib.parse import urlparse


#define variables
bad_chars = [',', '.', '/', '\\', '"', "'", '#', '©', '&', '<', '>', '-', '_', '=', '*', '(', ')', '$', '']
bad_words = ['and', 'the', 'it', 'or', 'a', 'then', 'next', 'i', 'form', 'here', 'to', 'new', 'me', 'use', 'using', 'free', 'have', 'about', 'contact',
'donate', 'home', 'up', 'is', 'all', 'for', 'more', 'with', 'on', 'of']


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#get arguments from input
def get_arguments():
	parser = argparse.ArgumentParser(description='')
	parser.add_argument('-u', dest='url', type=str, help='URL to scrape, ex: https://example.com', required=True)
	parser.add_argument('-l', dest='len_entered', type=int, help='Length of words to exclude, ex: "-l 4" would remove all words 4 characters or less')
	parser.add_argument('-c', dest='word_count', action='store_true', help='Count how many times each word appears in the list and prints them to the terminal')
	parser.add_argument('-o', dest='output', type=str, help='Output the main list of words to a file')
	parser.add_argument('-a', dest='alllinks_scrape', action='store_true', help='Scan the main page for any links, then fetch all text from those pages')
	parser.add_argument('-t', dest='transform', type=str, help='Add transforms to the words, choices are: lower, upper, 1337, add or cap')
	args = parser.parse_args()
	return args


#check if the URL is up
def check_url(url):
	try:
		r = requests.get(url)
		if r.status_code == 200:
			return True, r.status_code
		else:
			return False
	except requests.exceptions.RequestException as e:
		print(f'{bcolors.FAIL}[+]{bcolors.ENDC} Connection error on {url}, exiting now')
		sys.exit()



#define tags that will be scraped
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


#get and return the text from the page
def get_text_from_page(url):
	r = requests.get(url)
	soup = BeautifulSoup(r.content, 'html.parser')
	texts = soup.findAll(text=True)
	visible_texts = filter(tag_visible, texts)  
	return u" ".join(t.strip() for t in visible_texts)


	


#if the URL is up, get the text and put it in a list
def create_list(url, status_result):
	if status_result == True:
		all_text = get_text_from_page(url)
	else:
		print("URL is not up, exiting now")
		sys.exit()
	split_text = all_text.split()
	return split_text


#remove bad characters from the list
def remove_bad_chars(bad_chars, split_text):
	for item in bad_chars:
		for line in split_text:
			if item == line:
				split_text.remove(line)
	return split_text


#remove simple words from the list
def remove_bad_words(bad_words, split_text):
	for item in bad_words:
		for line in split_text:	
			if item == line.lower():
				split_text.remove(line)
	return(split_text)	


#remove words less than specified characters, if arg
def remove_words_less_than(len_entered, split_text):
	new_list = []
	for line in split_text:
		if len(line) > len_entered:
			new_list.append(line)
	return new_list


#calculate how many times a word appears in the list
def calculate_word_count(split_text):
	return collections.Counter(split_text).most_common()


#print the word count to the screen
def print_word_count(split_text):
	list_to_print = calculate_word_count(split_text)
	for line in list_to_print:
		a, b = line
		print(f'{a} : {b}')


#remove trailing punctuation, ex: . and ,
def remove_punctuation(split_text):
	another_list = []
	for line in split_text:
		another_list.append(line.strip(punctuation))
	return another_list


#write the final list to a file
def write_to_file(split_text, output):
	with open(output, 'w+') as f:
		for word in split_text:
			f.write(word + '\n')
		f.close()


#get list of links from the main page
def get_links_from_mainURL(url):
	link_list = []
	second_list = []
	final_list = []
	maindomain = urlparse(url).netloc
	r = requests.get(url)
	soup = BeautifulSoup(r.content, 'html.parser')
	for link in soup.findAll('a'):
		link_list.append(link.get('href'))
	for item in link_list:
		if 'http' in item:
			second_list.append(item)
		else:
			second_list.append(url + item)
	for item in second_list:
		checkdomain = urlparse(item).netloc
		if maindomain == checkdomain:
			final_list.append(item)


	return final_list


#fetch the text from each link and add it to the list of words
def fetch_text_from_all_links(list_of_links, split_text):
	filtered_link_list = []
	[filtered_link_list.append(x) for x in list_of_links if x not in filtered_link_list]
	for link in filtered_link_list:
		try:
			print(f'{bcolors.OKCYAN}[+]{bcolors.ENDC} Fetching text from {link}')
			page_text = get_text_from_page(link)
			newlist = page_text.split()
			for item in newlist:
				split_text.append(item)
		except:
			print(f'{bcolors.FAIL}[+]{bcolors.ENDC} Connection error on {link}')
			pass			


def transform_list(transform, filtered_list):
	transform_list = []
	if transform == '1337':
		transform_list = transformation_1337(filtered_list)
	elif transform == 'upper':
		for word in filtered_list:
			transform_list.append(word.upper())
	elif transform == 'lower':
		for word in filtered_list:
			transform_list.append(word.lower())
	elif transform == 'add':
		string_to_add = input("Enter character(s) to be added to the end of every word: ")
		for line in filtered_list:
			transform_list.append(line + string_to_add)
	elif transform == 'cap':
		for line in filtered_list:
			transform_list.append(line.capitalize())

	else:
		print("Transform type not found, exiting now")
		sys.exit()
	return transform_list


def transformation_1337(filtered_list):
	transformed_list = []
	replacements = ( ('a','4'), ('e','3'),('l','1'), ('o','0'), ('t','+') )
	for word in filtered_list:
		new_word = word
		for old, new in replacements:
			new_word = new_word.replace(old, new)
		transformed_list.append(new_word)
	return transformed_list


def print_banner():
	print("""\
	 ____        _   _                 
	|  _ \ _   _| |_| |__   ___  _ __  
	| |_) | | | | __| '_ \ / _ \| '_ \ 
	|  __/| |_| | |_| | | | (_) | | | |
	|_|    \__, |\__|_| |_|\___/|_| |_|
	       |___/                       
__        __   _    ____                                 
\ \      / /__| |__/ ___|  ___ _ __ __ _ _ __   ___ _ __ 
 \ \ /\ / / _ \ '_ \___ \ / __| '__/ _` | '_ \ / _ \ '__|
  \ V  V /  __/ |_) |__) | (__| | | (_| | |_) |  __/ |   
   \_/\_/ \___|_.__/____/ \___|_|  \__,_| .__/ \___|_|   
                                        |_|             

		""")

#main function
def main():
	print_banner()
	#get user arguments and check if URL is up
	args = get_arguments()
	status_result, status_code = check_url(args.url)
	print('*' * 50 + '\n')
	print(f"{bcolors.OKGREEN}[+]{bcolors.ENDC} Checking if the URL is up, response code: {bcolors.OKBLUE}{status_code}{bcolors.ENDC}")
	print('\n' + '*' * 50)


	#get list of urls and create initial list from the main page, do alllinks scrape if specified
	print('*' * 50 + '\n')
	print(f"{bcolors.OKGREEN}[+]{bcolors.ENDC} Creating initial list of words from the given URL: {bcolors.OKBLUE}{args.url}{bcolors.ENDC}\n")
	list_of_links = get_links_from_mainURL(args.url)
	split_text = create_list(args.url, status_result)
	if args.alllinks_scrape:
		print(f"{bcolors.OKGREEN}[+]{bcolors.ENDC} Alllinks option selected, gathering links from {args.url} page and scraping text\n")
		fetch_text_from_all_links(list_of_links, split_text)
		print('\n')
	print('*' * 50)

	#format the list to be handled
	if args.len_entered:
		split_text = remove_words_less_than(args.len_entered, split_text)
	split_text = remove_punctuation(split_text)
	split_text = remove_bad_chars(bad_chars, split_text)
	split_text = remove_bad_words(bad_words, split_text)

	if args.word_count:
		print('*' * 50 + '\n')
		print(f"{bcolors.OKGREEN}[+]{bcolors.ENDC} Count of each word in the list\n")
		print_word_count(split_text)
		print('\n' + '*' * 50)

	#remove duplicates from list, enter transformations here, lower, upper and 1337speak etc.
	filtered_list = []
	[filtered_list.append(x) for x in split_text if x not in filtered_list]
	if args.transform:
		print('*' * 50 + '\n')
		print(f"{bcolors.OKGREEN}[+]{bcolors.ENDC} Transforming the list with given mode: {args.transform}")
		filtered_list = transform_list(args.transform,filtered_list)
		print('\n' + '*' * 50)


	#output options, word count etc.
	if args.output:
		print('*' * 50 + '\n')
		print(f"{bcolors.OKGREEN}[+]{bcolors.ENDC} Writing list to file: {args.output}")
		write_to_file(filtered_list, args.output)

	print(f'\n\n{bcolors.OKGREEN}[+]{bcolors.ENDC} Program completed, exiting now')

	print('\n' + '*' * 50)

if __name__=="__main__":
	main()
