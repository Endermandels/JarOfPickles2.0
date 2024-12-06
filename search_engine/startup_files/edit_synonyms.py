import os, json

def main():
	path = os.path.dirname(os.path.realpath(__file__))
	os.chdir(path)

	found = {}
	synonyms_dic = None

	with open("synonyms.json", "r") as f:
		synonyms_dic = json.load(f)

	for japan_title in synonyms_dic:
		synonym = synonyms_dic[japan_title][0]
		if synonym not in found: found[synonym] = [japan_title]
		else: found[synonym].append(japan_title)

	temp = found.copy()
	for j in temp:
		if len(temp[j]) == 1: found.pop(j)

	print(f"{len(found)} synonyms mapped to multiple Japanese titles")

	for synonym in found:
		count = 0
		print(synonym)
		for titles in found[synonym]:
			print(f"\t{titles} ({count})")
			count += 1
		while (True):
			x = input("Choose: ")
			if x == "none":
				for titles in found[synonym]: synonyms_dic.pop(titles)
				break
			else:
				try:
					x = int(x)
					found[synonym].pop(x)
					for titles in found[synonym]: synonyms_dic.pop(titles)
					break
				except:
					print("try again")

	with open("edited_synonyms.json", "w") as f:
		json.dump(synonyms_dic,f, indent=4)


if __name__ == '__main__':
	main()