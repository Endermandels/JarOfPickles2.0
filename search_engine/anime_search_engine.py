from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import *
from whoosh.analysis import StemmingAnalyzer, SimpleAnalyzer
from whoosh.qparser import QueryParser
from whoosh.searching import ResultsPage
from whoosh import scoring

from bs4 import BeautifulSoup
from fast_autocomplete import AutoComplete, autocomplete_factory
from fast_autocomplete.misc import *

from gensim.models import Word2Vec

import os, pickle, re, string

# This function is needed because the scoring.FunctionWeighting.FunctionScorer
# needs a max_quality function.
def max_quality(self):
	return 9999

class SearchEngine(object):

	def __init__(
		self, 
		index_dir = "./indexdir", 
		url_map_file = "./sample/url_map.dat", 
		docs_raw_dir = "./sample/_docs_raw/", 
		docs_cleaned_dir = "./sample/_docs_cleaned/",
		page_rank_file = "./startup_files/page_rank.dat", 
		titles_json = "./startup_files/titles.json", 
		synonyms_json="./startup_files/synonyms.json", 
		word_2_vec_model = "./startup_files/word2vec.model",
		debug = False
	):
		# File and directory attributes
		self.debug = debug
		self.index_dir = index_dir
		self.page_rank_file = page_rank_file
		self.url_map_file = url_map_file
		self.docs_raw_dir = docs_raw_dir
		self.docs_cleaned_dir = docs_cleaned_dir
		# Whoosh index/scoring attributes
		self.schema = Schema(title=TEXT(stored=True, analyzer=SimpleAnalyzer()), url = ID(stored=True), content=TEXT(analyzer=StemmingAnalyzer()))
		self.ix = self.__get_indexer()
		self.size = self.ix.doc_count()
		self.page_rank = self.__unpickle(page_rank_file)
		assert self.size == len(self.page_rank), "the index and page rank don't match"
		# Whoosh Paging Attributes
		custom_weighting = scoring.FunctionWeighting(self.__custom_scorer)
		custom_weighting.FunctionScorer.max_quality = max_quality
		self.searcher = self.ix.searcher(weighting=custom_weighting)
		self.current_result = None
		self.current_query = None
		self.current_page = 1
		self.scoring_type = "both"
		self.word_2_vec_model = Word2Vec.load(word_2_vec_model)

		content_files = {
			"synonyms": {"filepath": synonyms_json, "compress": False},
			"words": {"filepath": titles_json, "compress": True}
		}
		self.autocomplete = autocomplete_factory(content_files=content_files)

	# Returns an existing or new indexer 
	def __get_indexer(self):
		if not os.path.exists(self.index_dir): os.mkdir(self.index_dir)
		if not exists_in(self.index_dir): return self.__create_index()
		else: return open_dir(self.index_dir)

	# Get url map from path file
	def __unpickle(self, path):
		data = None
		with open(path,"rb") as f:
			data = pickle.load(f)
		return data

	# Returns a new indexer with a Whoosh Index
	def __create_index(self):
		ix = create_in(self.index_dir, self.schema)
		writer = ix.writer(limitmb=1024, procs=4, multisegment=True)
		urls = self.__unpickle(self.url_map_file)
		_title = ""
		_content = ""
		count = 1
		# For each url mapped to a file name
		for u in urls:
			file_name = urls[u]
			# Get the title for the file name
			with open(self.docs_raw_dir+file_name, "r", encoding="utf-8") as html:
				_title = BeautifulSoup(html.read(), "lxml").title.string.strip()
				_title = re.sub(r"(\s*-\s*myanimelist\.net\s*)$", "", _title.lower())
			# Get the text content for the file name
			with open(self.docs_cleaned_dir+file_name, "r", encoding="utf-8") as text:
				_content = text.read()

			if self.debug: print(f"({count}) Indexing {_title}")

			writer.add_document(title=_title, url=u, content=_content)
			count += 1
		writer.commit()
		return ix

	def change_scoring_type(self, type):
		allowed_types = ["both", "bm25", "pagerank"]
		if type in allowed_types: self.scoring_type = type
	
	def get_scoring_type(self):
		return self.scoring_type

	# Combines page rank and bm25 to be used with whoosh.scoring.FunctionWeighting
	def __custom_scorer(self, searcher, fieldname, text, matcher):
		url = searcher.stored_fields(matcher.id())["url"]
		pr = self.page_rank[url]
		bm25 = scoring.BM25F().scorer(searcher, fieldname, text).score(matcher)
		a = 0
		b = 0
		if self.scoring_type in ["both", "pagerank"]: a = 100000 # Most PageRank is 1E-6 place
		if self.scoring_type in ["both", "bm25"]: b = 1.5
		return a*pr + b*bm25

	# Updates current_query and current_result for a given string and upgrade option
	def submit_query(self, query_string, upgrade=False, relev_results=False):
		self.current_page = 1
		self.current_query = query_string
		self.current_result = self.get_result(query_string, upgrade=upgrade)
		if relev_results: self.current_result = self.__get_relevant_results()

		if self.debug: print(f"\"{query_string}\" WAS SUBMITTED")

	# Returns a new query created with Fast Autocomplete from a string.
	# If only the last word of the string needs to be auto completed,
	# whole_string should be set to True, and the last_word_index should be
	# the index of where the first letter of the word begins.
	def get_suggested_query(self, string, last_word_index, whole_string=False):
		if whole_string: last_word_index = 0
		results = self.autocomplete.search(word=string[last_word_index:], max_cost=5, size=3)

		if not results: return string
		if whole_string:
			# result = "' OR '".join(results[0])
			result = "' OR '".join([word for inner_list in results for word in inner_list])
			return f"'{result}'"
		else:
			result = (results[0][0]).strip()
			return string[0:last_word_index]+result

	# Returns a whoosh.searching.results object for a given string
	# Setting upgrade to True uses whoosh.searching.results.upgrade().
	# A given string is converted with Fast Autocomplete and used to
	# upgrade the Fast Autocomplete result.
	def get_result(self, query_string, upgrade=False):
		query_obj = QueryParser("title", self.ix.schema).parse(query_string)
		query_result = self.searcher.search(query_obj, limit=None)
		if not upgrade: return query_result

		query_obj2 = QueryParser("content", self.ix.schema).parse(query_string)
		query_result2 = self.searcher.search(query_obj2, limit=None)

		suggested_query = self.get_suggested_query(query_string, 0, whole_string=True)
		suggested_query_obj = QueryParser("title", self.ix.schema).parse(suggested_query)

		suggested_result = self.searcher.search(suggested_query_obj, limit=None)
		suggested_result.upgrade(query_result)
		suggested_result.extend(query_result2)
		return suggested_result

	# Based on the results in self.current_result, return relevant results.
	# Relevant results are determined by taking the top 2 documents in
	# self.current_result and getting the top 2 most related term to each term
	# in the query.
	#
	# The related terms are then used to from several queries to pass in the
	# get_result method in which all the results from the queries are appended
	# and then returned. 
	def __get_relevant_results(self, k=2, debug=False):
		count = 0
		results = self.return_page(1)["docs"]
		model = self.word_2_vec_model.wv

		all_results = None
		for result in results:
			if count == k: break

			terms = result["title"].translate(str.maketrans(
				'', '', string.punctuation))
			terms = list(set(terms.split()))
			if debug: print(f"Terms: {terms}")

			related_terms = []
			for term in terms:
				similar_terms = model.most_similar(term, topn=k)
				similar_terms.insert(0, (term, 1))
				related_terms.append(similar_terms)

			indexes = [0] * len(related_terms)
			for _ in range(k):
				query, indexes = self.__get_next_related_query(related_terms, indexes)
				if debug: print(f"Related query is: {query}")
				if not all_results: all_results = self.get_result(query)
				all_results.upgrade_and_extend(self.get_result(query))

			count += 1

		return all_results

	# Returns what the next query is based on the related_terms and indexes.
	# Also returns the updated array of indexes 
	# (index corresponds to a row in related_terms).
	#
	# related_terms is an array of tuples. Each tuple has 2 elements.
	# The first element is the term as a string and the second element
	# is a score from 0 to 1 on how relevant that term is.
	# Row is the row to get the related_terms.
	def __get_next_related_query(self, related_terms, indexes):
		max_score = 0
		max_index = 0
		for i in range(len(indexes)):
			indexes[i] += 1
			score = self.__get_relevance_score(related_terms, indexes)
			if score > max_score:
				max_score = score
				max_index = i
			indexes[i] -= 1

		indexes[max_index] += 1

		query = []
		for i in range(len(indexes)):
			j = indexes[i]
			query.append(related_terms[i][j][0])
		query = " OR ".join(query)
		return query, indexes

	# Gets the relevance score based on the related_terms and array of
	# indexes (index corresponds to a row in related_terms).
	# related_terms is an array of tuples. Each tuple has 2 elements.
	# The first element is the term as a string and the second element
	# is a score from 0 to 1 on how relevant that term is.
	def __get_relevance_score(self, related_terms, indexes):
		score = 0
		for i in range(len(indexes)):
			j = indexes[i]
			score += related_terms[i][j][1]
		return score

	# Returns a dictionary representation of a page result
	def return_page(self, page_num):
		results = {}
		if self.current_result == None: 
			print("Submit a query first")
			return results

		if page_num < 1: page_num = 1

		page_result = ResultsPage(self.current_result, page_num)
		self.current_page = page_result.pagenum
		
		results['total'] = page_result.total
		results['docs'] = []
		
		for result in page_result:
			results['docs'].append({'title': result['title'], 'url': result['url']}) 
		
		return results

	# Prints the page_num page for a result dictionary
	def print_page(self, result_dic):
		print(f"--------------------\n{result_dic["total"]} RESULTS")
		if result_dic["total"] == 0: print("No results found")
		for result in result_dic["docs"]: print(f'{result["title"]}\n\t\033[94m{result["url"]}\033[0m\n')
		print(f"PAGE {self.current_page}")
		print("--------------------")

	# Returns a page result dictionary for a page one higher than self.current_page for self.current_query
	def get_next_page(self):
		if self.current_result == None: print("Submit a query first")
		else:
			self.current_page += 1
			page_result = self.return_page(self.current_page)
			if self.debug: self.print_page(page_result)
			return page_result

	#  Returns a page result dictionary for a page one lower than self.current_page for self.current_query
	def get_prev_page(self):
		if self.current_result == None: print("Submit a query first")
		else:
			self.current_page -= 1
			page_result = self.return_page(self.current_page)
			if self.debug: self.print_page(page_result)
			return page_result

	#  Returns a page result dictionary for page one for self.current_query
	def get_first_page(self):
		if self.current_result == None: print("Submit a query first")
		else:
			self.current_page = 1
			page_result = self.return_page(self.current_page)
			if self.debug: self.print_page(page_result)
			return page_result

	# Closes the searcher that is opened during initialization
	def close_searcher(self):
		self.searcher.close()

# Terminal demo modified from fast_autocomplete.demo
def demo(search_engine):
	search_engine.change_scoring_type("both")
	word_list = []
	start_of_words = [0]
	cursor_index = 0
	last_result = None
	query = ""
	print("Demo started. Type something (exit with ctrl+c)")
	while (True):
		pressed = read_single_keypress()
		print(pressed)
		# Exit with ctrl+c
		if pressed == '\x03': break # \x03 is ctrl+c
		# Backspace character is pressed
		elif pressed == '\x7f':
			if word_list:
				cursor_index -= 1
				char = word_list.pop()
				# Update the start_of_words if a word is deleted
				if (word_list and word_list[-1] == ' ' and char != ' '): start_of_words.pop()
		# Tab character is pressed, use auto-complete
		elif pressed == '\x09':
			# Create a list of indices to update start_of_words if the result has space characters
			new_string_array = list(search_engine.get_suggested_query(query,start_of_words[-1])[start_of_words[-1]:])
			indices = [i for i, x in enumerate(new_string_array) if x == ' ']

			if indices:
				new_indices = []
				for i in range(len(indices)):
					if i+1 < len(indices) and indices[i+1] == indices[i]+1: continue
					new_indices.append(indices[i])
				if indices[-1] == len(new_string_array)-1: new_indices.pop()
			
				indices = [x+1+start_of_words[-1] for x in new_indices]
			# Replace the last word with the result
			word_list = word_list[0:start_of_words[-1]] + new_string_array
			cursor_index = start_of_words[-1]+len(new_string_array)
			start_of_words += indices
		elif pressed == '!':
			search_engine.get_prev_page()
			continue
		elif pressed == '@':
			search_engine.get_next_page()
			continue
		else:
			if word_list and word_list[-1] == ' ' and pressed != ' ': start_of_words.append(cursor_index)
			word_list.append(pressed)
			cursor_index += 1

		print(chr(27) + "[2J")
		query = ''.join(word_list)
		print(query+"_")
		print("Last word:", start_of_words[-1])
		print("Current cursor:", cursor_index)
		print("Current word:", ''.join(word_list[start_of_words[-1]:]))

		search_engine.submit_query(query, upgrade=True, relev_results=True)

		# suggested_query = search_engine.get_suggested_query(query,0, whole_string=True)
		# search_engine.submit_query(suggested_query, upgrade=False)

		search_engine.print_page(search_engine.return_page(1))

def main():
	# string = "fairy tail manga"
	print("initializing search engine...")
	mySearchEngine = SearchEngine(
		debug=True,
		url_map_file="./new_sample/url_map.dat",
		docs_raw_dir ="./new_sample/_docs_raw/",
		docs_cleaned_dir="./new_sample/_docs_cleaned/")
	# mySearchEngine.submit_query(string, upgrade=True, relev_results=True)
	# mySearchEngine.get_first_page()
	print("starting demo...")
	demo(mySearchEngine)
	mySearchEngine.close_searcher()

if __name__ == "__main__":
	main()
