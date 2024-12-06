from whoosh.searching import ResultsPage
from anime_search_engine import SearchEngine
from time import time

def return_page(results, page_num):
	results_dic = {}

	if page_num < 1: page_num = 1

	page_result = ResultsPage(results, page_num)

	results_dic['total'] = page_result.total
	results_dic['docs'] = []
	
	for result in page_result:
		results_dic['docs'].append({'title': result['title'], 'url': result['url']}) 
	
	return results_dic

def test_search_engine_init():
	print("Testing search engine init...")
	iterations = 20
	total_time = 0

	for i in range(iterations):
		se = None
		start = time()
		se = SearchEngine(
			index_dir = "./indexdir", 
			url_map_file = "./new_sample/url_map.dat", 
			docs_raw_dir = "./new_sample/_docs_raw/", 
			docs_cleaned_dir = "./new_sample/_docs_cleaned/",
			page_rank_file = "./startup_files/page_rank.dat", 
			titles_json = "./startup_files/titles.json", 
			synonyms_json="./startup_files/synonyms.json", 
			word_2_vec_model = "./startup_files/word2vec.model",
			debug = False
		)
		end = time()
		init_time = end - start
		total_time += init_time
		print(f"{init_time}")

	average_time = total_time/iterations
	print(average_time)


def test_searching(anime_list, relev_results=False):
	print("Testing searching...")
	anime_index = 0
	iterations = 20
	total_animes = len(anime_list)
	anime_results = [None]*total_animes

	se = SearchEngine(
		index_dir = "./indexdir", 
		url_map_file = "./new_sample/url_map.dat", 
		docs_raw_dir = "./new_sample/_docs_raw/", 
		docs_cleaned_dir = "./new_sample/_docs_cleaned/",
		page_rank_file = "./startup_files/page_rank.dat", 
		titles_json = "./startup_files/titles.json", 
		synonyms_json="./startup_files/synonyms.json", 
		word_2_vec_model = "./startup_files/word2vec.model",
		debug = False
	)

	for anime in anime_list:
		print(f"\ttesting {anime}")
		total_time = 0

		try:
			for i in range(iterations):
				start = time()
				se.submit_query(anime, upgrade=True, relev_results=relev_results)
				end = time()
				search_time = end - start
				total_time += search_time
				print(f"\t\t{search_time}")

				if i == 0: anime_results[anime_index] = se.current_result

			average_time = total_time/iterations
			print(f"\t\taverage: {average_time}")
			anime_index += 1
		except KeyError:
			anime_index += 1
			print("Error with Word2Vec")
			continue

	for results in anime_results:
		se.print_page(return_page(results, 1))


def main():
	anime_list = [
		"terra formars",
		"kikansha no mahou wa tokubetsu desu",
		"shiguang dailiren",
		"soukou no strain",
		"hikaru no go",
		"mikagura gakuen kumikyoku",
		"dance dance danseur",
		"deaimon",
		"mamahaha no tsurego ga motokano datta",
		"chainsaw man",
		"magi: the labyrinth of magic",
		"flcl",
		"days",
		"shikizakura",
		"aharen-san wa hakarenai",
		"usakame",
		"wotaku ni koi wa muzukashii",
		"uchuu kyoudai",
		"tensai ouji no akaji kokka saisei jutsu",
		"yurei deco"
	]
	# test_search_engine_init()
	test_searching(anime_list[0:10], relev_results=False)

	


if __name__ == '__main__':
	main()