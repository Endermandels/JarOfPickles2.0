# JarOfPickles

# Install Dependencies
Inside the main directory do

	pip install -r "requirements.txt"


# Running the project
1. Change directory to front_end/
2. Run app.py with "python3 app.py"
3. Wait until a URL appears in the terminal (Ex. http://127.0.0.1:5000)
4. Copy and paste the URL into a web browser, and allow it to load

# The sample

The "/search_engine/new_sample/\_docs_cleaned" and "/search_engine/new_sample/\_docs_raw" directories must have a set of regular text and HTML text, respectively. The file in one directory must correspond to the other directory by having the same file names.

A "/search_engine/new_sample/url\_map.dat" file must exist, where the file is a pickled dictionary that maps a URL to it's corresponding file name in "/search_engine/new_sample/\_docs\_cleaned" and "/search_engine/new_sample/\_docs_raw".

There must be a pickled Pandas DataFrame in "./new_sample/adjacency_matrix.dat", where the rows and columns are list of URLs. The data stored is the total number of URL links from the row URL to the column URL. If you decide to crawl again using crawler.py, you must do the following inside the "/search_engine/new_sample" directory.

	python3 ../../crawler/build_adj_matrix.py -d
	python3 ../../crawler/build_adj_matrix.py -m

Ex matrix.
,	url1,	url2,	url3  
url1,	2,	0,	1  
url2,	0,	3,	1  
url3,	0,	0,	1  


# Running anime_search_engine.py

You must be inside the "search_engine" directory for it to work with the default hard-coded directories.

	python3 anime_search_engine.py


# Running page_rank.py

Using the following command will create a pickle file, named "page_rank.dat", that stores a dictionary mapping URLs to their PageRank score. There must be a complete sample to run properly. You must be inside the "search_engine/startup_files" directory to use the command.

	python3 page_rank.py


# Running word_2_vec_model.py

The following command will create the necessary word2vec models to use for related results in anime_search_engine.py. There must be a complete sample to run properly. You must be inside the "search_engine/startup_files" directory to use the command.

	python3 word_2_vec_model.py


# Building anime_search_engine.py

In the search_engine directory these directories/files must exist:
- indexdir/
- page_rank.dat
- synonyms.json
- titles.json
- word2vec.model

If the indexdir directory doesn't exist in the search_engine directory, the sample must be complete to automatically create the index.

There must be a "search_engine/startup_files/page_rank.dat" file. See "Running page_rank.py".

There must be a "search_engine/startup_files/word2vec.model" file. See "Running word_2_vec_model.py".

A "titles.json" and "synonyms.json" file must exist in the "/search_engine/startup_files" directory. If the "/search_engine/new_sample" directory is complete, then these files can be built by running the following command in the "startup_files" directory.

	python3 get_titles.py

You can create a search engine with SearchEngine()

If directories/files have been changed, then you must alter the following parameters to indicate where they are located.

index_dir,
url_map_file,
docs_raw_dir,
docs_cleaned_dir,
page_rank_file,
titles_json,
synonyms_json, 
word_2_vec_model

Submit a query with:

	SearchEngine.submit_query("some_string")

You can optionally set upgrade and relev_results to True or False. Upgrade enables autocomplete, relev_results enables the related results features.

You can get back the results for a page with:

	SearchEngine.return_page(page_num)

You can print the results with:

	SearchEngine.print_page(returned_page)

You must close the searcher when finished with the search engine with:

	SearchEngine.close_searcher()

Ex.  
	string = "tokyo"  
	mySearchEngine = SearchEngine() 
	mySearchEngine.submit_query(string, upgrade=True)
	mySearchEngine.print_page(mySearchEngine.return_page(1))