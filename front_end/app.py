import os
import sys
import inspect
import requests
from http.client import responses


# Move CWD to parent dir to have access to search_engine
# Code from https://stackoverflow.com/questions/714063/importing-modules-from-parent-folder
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

from flask import Flask, render_template, request, redirect, jsonify
from search_engine.anime_search_engine import SearchEngine
import pickle


app = Flask(__name__)

@app.route('/')
def index():
    global last_q
    global show_related_results
    show_related_results = False
    last_q = None
    mySearchEngine.change_scoring_type('both')
    return render_template('index.html')

def link_status(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code
    except requests.RequestException:
        return 400
    
@app.route('/update-checkboxes', methods=['POST'])
def update_checkboxes():
    global show_related_results
    
    # Retrieve checkbox data from the JSON body
    data = request.json
    checked_boxes = data.get('checked', [])
    
    has_pagerank = 'pagerank' in checked_boxes
    has_bm25 = 'bm25' in checked_boxes
    has_related_results = 'related_results' in checked_boxes

    if has_pagerank and has_bm25:
        mySearchEngine.change_scoring_type('both')
    elif has_pagerank:
        mySearchEngine.change_scoring_type('pagerank')
    elif has_bm25:
        mySearchEngine.change_scoring_type('bm25')
    
    if has_related_results:
        show_related_results = True
    else:
        show_related_results = False

    print(f"Checked checkboxes: {checked_boxes}")
    
    current_scoring_type = mySearchEngine.get_scoring_type()

    # Return a response detailing which checkbox should be on
    return jsonify({"message": "Checkbox states updated", "checked": {
        'pagerank': current_scoring_type in ['both', 'pagerank']
        , 'bm25': current_scoring_type in ['both', 'bm25']
        , 'related_results': has_related_results
    }})


@app.route('/search')
def search():
    global last_q
    page = request.args.get('page') # pagination
    q = request.args.get('q') # query
    print(page)
    print(q)
        
    if page and last_q:
        if page not in ['next', 'prev', 'first']:
            print('invalid page request')
        else:
            if page == 'next':
                results = mySearchEngine.get_next_page()
            elif page == 'prev':
                results = mySearchEngine.get_prev_page()
            elif page == 'first':
                results = mySearchEngine.get_first_page()
                
            if results:
                results = results['docs']
                for result in results:
                    result['filtered_url'] = 'check_url?u=' + result['url']
                return render_template("search_results.html", results=results, url_to_image=images_dict)    
    
    if not q and last_q:
        q = last_q
    else:
        last_q = q
    
    results = []
    
    if q and mySearchEngine:
        mySearchEngine.submit_query(q, upgrade=True, relev_results=show_related_results)
        results = mySearchEngine.return_page(1)['docs']
        for result in results:
            result['filtered_url'] = 'check_url?u=' + result['url']
       
    return render_template("search_results.html"
                           , results=results
                           , url_to_image=images_dict)

@app.route('/check_url')
def check_url():
    url = request.args.get('u') # url to check
    status = link_status(url)
    if status != 200:
        return render_template('error.html', status=status, description=responses[status])
    return redirect(url) 

def unpickle(fn):
    try:
        with open(fn, 'rb') as file:
            data = pickle.load(file)
        return data
    except Exception as e:
        print(f"Error unpickling {fn}: {e}")
        sys.exit(1)

def start_app():
    global mySearchEngine
    global images_dict
    global last_q
    global show_related_results
    show_related_results = False
    last_q = None
    dir = 'search_engine'
    images_dict = unpickle(f'../{dir}/startup_files/image_dict.dat')
    mySearchEngine = SearchEngine(
        debug=True
        , index_dir=f'../{dir}/indexdir'
        , page_rank_file=f'../{dir}/startup_files/page_rank.dat'
        , titles_json=f'../{dir}/startup_files/titles.json'
        , synonyms_json=f'../{dir}/startup_files/synonyms.json'
        , url_map_file=f'../{dir}/new_sample/url_map.dat'
        , docs_raw_dir=f'../{dir}/new_sample/_docs_raw/'
        , docs_cleaned_dir=f'../{dir}/new_sample/_docs_cleaned/'
        , word_2_vec_model=f'../{dir}/startup_files/word2vec.model')
    app.run(debug=True)
    mySearchEngine.close_searcher()

if __name__ == '__main__':
    start_app()