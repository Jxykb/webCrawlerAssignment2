def tokenize():
    links = []
    file = open("Logs/Worker.log", 'r')
    for line in file:
        first = line[55:]
        link = first.split(',')[0]
        url = ""
        if '#' in link:
            url = link.split("#")[0]
        else:
            url = link
        if url:
            links.append(url)
    file.close()
    return links

def computeUniqueLinks(tokenList):
    tokenDict = {}
    for token in tokenList:
        if token in tokenDict:
            tokenDict[token] += 1
        else:
            tokenDict.update({token: 1})
    return tokenDict

def printFrequencies(tokenDict):
    list2 = []
    for key in tokenDict.keys():
        list2.append([key, tokenDict[key]])
    for i in list2:
        print(i[0], i[1], sep=" -> ")
    print(f"Total Unique: {len(tokenDict)}")

if __name__ == "__main__":
    tokenList = tokenize()
    tokenDict = computeUniqueLinks(tokenList)
    printFrequencies(tokenDict)
