from bs4 import BeautifulSoup
from threading import Thread
import pickle, re, os, json

count = 0
titles_dic = {}
synonyms_dic = {}
TOTAL = None

# Removes clutter from titles
def clean_title(title):
	global synonyms_dic
	title = title.lower().strip()
	title = re.sub(r"(\s*-\s*myanimelist\.net\s*)$", "", title)
	title = re.sub(r"(\s*\|\s*.+)$", "", title)

	match = re.search(r"(\s*\(.+\)\s*)$", title)
	if (match):
		title = re.sub(r"(\s*\(.+\)\s*)$", "", title)
		synonyms_dic[title] = [match.group().strip(" ()")]
	return title

# Unpickles pickle files
def __unpickle(path):
	data = None
	with open(path,"rb") as f:
		data = pickle.load(f)
	return data

# Adds titles for a given start and stop range for a list of urls.
# urls is a dictionary mapping urls to file names.
# url_list is a list of urls. docs_raw_dir is the path to _docs_raw
def get_titles(start, stop, urls, url_list, docs_raw_dir):
	_title = ""
	_popularity = 0
	global count
	global titles_dic

	for u in url_list[start:stop]:
		file_name = urls[u]
		# Get the title for the file name
		with open(docs_raw_dir+file_name, "r") as html:
			html_parser = BeautifulSoup(html.read(), "lxml")
			_title = html_parser.title.string
			cleaned_title = clean_title(_title)
			try:
				_popularity = (html_parser.find("span", class_="numbers popularity").find("strong").text.strip())[1:]
				_popularity = int(_popularity)
			except AttributeError:
				_popularity = 99999
			titles_dic[cleaned_title] = [{}, None, 99999-_popularity]

		print(f"({count}) got {cleaned_title}: {_popularity}")
		count += 1

# Pickles a dictionary mapping titles to an empty dictionary
def main():
	global TOTAL
	path = os.path.dirname(os.path.realpath(__file__))
	os.chdir(path)
	sample_dir = "sample_copy"
	docs_raw_dir = f'../{sample_dir}/_docs_raw/'

	thread_num = 8
	threads = [None]*thread_num
	ranges = [0]*thread_num
	urls = __unpickle(f'../{sample_dir}/url_map.dat')
	url_list = list(urls.keys())
	total = TOTAL if TOTAL else len(urls)-1
	global titles_dic
	for i in range(thread_num):
		if i == 0:
			ranges[0] = total//thread_num
		else:
			ranges[i] = ranges[i-1]+total//thread_num
		if i == thread_num-1:
			ranges[i] += total-ranges[i]

	for i in range(thread_num):
		start = 0;
		end = 0;
		if i == 0:
			start = 0
		else:
			start = ranges[i-1]
		end = ranges[i]
		threads[i] = Thread(target = get_titles, args = (start, end, urls, url_list, docs_raw_dir))
	
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()

	with open("titles.json","w") as f:
		json.dump(titles_dic,f, indent=4)

	with open("synonyms.json","w") as f:
		json.dump(synonyms_dic,f, indent=4)


if __name__ == '__main__':
	main()