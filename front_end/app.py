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


app = Flask(__name__)

@app.route('/')
def index():
    global last_q
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
    # Retrieve checkbox data from the JSON body
    data = request.json
    checked_boxes = data.get('checked', [])

    if len(checked_boxes) == 2:
        mySearchEngine.change_scoring_type('both')
    elif len(checked_boxes) == 1:
        mySearchEngine.change_scoring_type(checked_boxes[0])

    print(f"Checked checkboxes: {checked_boxes}")

    # Return a response (optional)
    return jsonify({"message": "Checkbox states updated", "checked": checked_boxes})


@app.route('/search')
def search():
    global last_q
    page = request.args.get('page') # pagination
    q = request.args.get('q') # query
    print(page)
    print(q)
        
    if page and last_q:
        if page == 'next':
            results = mySearchEngine.get_next_page()
            if results:
                results = results['docs']
                for result in results:
                    result['url'] = 'check_url?u=' + result['url']
                return render_template("search_results.html", results=results)    
        elif page == 'prev':
            results = mySearchEngine.get_prev_page()
            if results:
                results = results['docs']
                for result in results:
                    result['url'] = 'check_url?u=' + result['url']
                return render_template("search_results.html", results=results)    
        else:
            print("invalid page request")
    
    if not q and last_q:
        q = last_q
    else:
        last_q = q
    
    results = []
    
    if q and mySearchEngine:
        mySearchEngine.submit_query(q, upgrade=True)
        results = mySearchEngine.return_page(1)['docs']
        for result in results:
            result['url'] = 'check_url?u=' + result['url']
       
    return render_template("search_results.html", results=results)

@app.route('/check_url')
def check_url():
    url = request.args.get('u') # url to check
    status = link_status(url)
    if status != 200:
        return render_template('error.html', status=status, description=responses[status])
    return redirect(url) 

def start_app():
    global mySearchEngine
    global last_q
    last_q = None
    dir = 'search_engine'
    mySearchEngine = SearchEngine(
        debug=True
        , index_dir=f'../{dir}/indexdir'
        , page_rank_file=f'../{dir}/startup_files/page_rank.dat'
        , titles_json=f'../{dir}/startup_files/titles.json'
        , synonyms_json=f'../{dir}/startup_files/synonyms.json'
        , url_map_file=f'../{dir}/new_sample/url_map.dat'
        , docs_raw_dir=f'../{dir}/new_sample/_docs_raw/'
        , docs_cleaned_dir=f'../{dir}/new_sample/_docs_cleaned/')
    app.run(debug=True)
    mySearchEngine.close_searcher()

if __name__ == '__main__':
    start_app()