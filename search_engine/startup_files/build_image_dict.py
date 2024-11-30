import pickle
from bs4 import BeautifulSoup

def main():
    with open('../new_sample/url_map.dat', 'rb') as file:
        url_map: dict = pickle.load(file)
    
    images = {}

    for url, docFN in url_map.items():
        with open('../new_sample/_docs_raw/' + docFN, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            
            image_tag = soup.find("meta", property="og:image")
            if image_tag and "content" in image_tag.attrs:
                # Assign the image URL to the corresponding row in the DataFrame
                images[url] = image_tag["content"]
    
    with open('./image_dict.dat', 'wb') as file:
        pickle.dump(images, file)
    
    # print(images)

if __name__ == '__main__':
    main()