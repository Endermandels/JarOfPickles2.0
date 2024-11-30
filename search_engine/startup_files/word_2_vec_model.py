from gensim.models import Word2Vec
from gensim.models import Phrases
import pickle, string

class create_word_2_vec_corpus(object):
	def __init__(self, url_map_file = "../new_sample/url_map.dat", 
		docs_cleaned_dir = "../new_sample/_docs_cleaned/", debug=False):
		self.url_map_file = url_map_file
		self.docs_cleaned_dir = docs_cleaned_dir
		self.debug = debug

	# Get url map from path file
	def __unpickle(self, path):
		data = None;
		with open(path, "rb") as f:
			data = pickle.load(f)
		return data

	def __iter__(self):
		urls = self.__unpickle(self.url_map_file)
		if self.debug: print("Starting new epoch")
		count = 1
		for u in urls:
			file_name = urls[u]
			with open(self.docs_cleaned_dir+file_name, "r") as text:
				text_no_punctuations = text.read().translate(
					str.maketrans('', '', string.punctuation)).lower()
				content = [word for word in text_no_punctuations.split()]
				yield content
			count += 1
			if self.debug and count % 10000 == 0: print(f"Count: {count}")

def main():
	corpus = create_word_2_vec_corpus(debug=True)
	model = Word2Vec(sentences=corpus, workers=8, epochs=3)
	model.save("word2vec.model")
	sims = model.wv.most_similar("fantasy", topn=10)
	for sim in sims:
		print(sim[0])

if __name__ == '__main__':
	main()
