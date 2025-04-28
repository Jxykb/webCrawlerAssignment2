import re
from urllib.parse import urlparse
from urllib.parse import urljoin

from bs4 import BeautifulSoup

import nltk
nltk.download('punkt')


DoNotCrawl = set()
Visited = set()
Commoners = dict()
LongestPage = ('Link', 0)
Subdomain = dict()

def scraper(url, resp):
    global DoNotCrawl
    links = extract_next_links(url, resp)
    valids = [link for link in links if is_valid(link)] #list of valid links

    if resp.status == 200:
        if url not in DoNotCrawl:
            wordsList = tokenize(resp)
            isLongestPage(url, len(wordsList))
            computeWordFrequencies(wordsList)
        
        commonWords() # writes the words from Commoners to common.txt (also see computeWordFrequencies for how Commoners is updated)
        unique()
        subdomainWrite()

    return valids


def extract_next_links(url, resp):
    global DoNotCrawl, Visited

    if resp.status != 200 or url in DoNotCrawl or url in Visited or resp.raw_response == None:
        DoNotCrawl.add(url)
        return set()

    Visited.add(url)

    subdomainCheck(url)

    # url parser
    parsed = urlparse(url)

    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    '''
    sentences = soup.getText().split('.')
    if not sentenceReps(sentences, #):
        DoNotCrawl.add(url)
        return set()
    '''
    list_of_links = set()

    links = soup.find_all('a', href=True)    
    for link in links:
        href = link.get('href')
        if parsed.netloc:
            href = urljoin(url, href) #check urljoin
        #checking for same links but fragmented with #
        href = href.split("#")[0]
        # maybe have to check for archive, evoke, swiki (185)
        if is_valid(href):
            list_of_links.add(href)
    return list_of_links

def tokenize(resp):
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    tokens = nltk.tokenize.word_tokenize(soup.get_text())
    words = [t.lower() for t in tokens if not re.match(r'[\W]+',t)]
    '''
    for token in tokens:
        word = ""
        for char in token:
            if char.isalnum() and char.isascii():
                word += char.lower()
            else:
                if word:
                    words.append(word)
                    word = ""
        if word: words.append(word)
    '''
    return words

def computeWordFrequencies(tokenList):
    global Commoners
    stopWords = [
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren", "t", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn", "did", "didn", "do", "does", "doesn", "doing", "don", "down", "during", "each", "few", "for", "from", "further", "had", "hadn", "has", "hasn", "have", "haven", "having", "he", "d", "ll", "s", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "m", "ve", "if", "in", "into", "is", "isn", "it", "its", "itself", "let", "me", "more", "most", "mustn", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan", "she", "should", "shouldn", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "re", "ve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn", "we", "were", "weren", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "won", "would", "wouldn", "you", "your", "yours", "yourself", "yourselves"
    ]

    for token in tokenList:
        if token not in stopWords and token.isalpha():
            Commoners[token] += 1

def wordCount(resp):
    tokens = tokenize(resp)
    return len(tokens) < 150

def isLongestPage(url, lengthOfPage):
    global LongestPage
    if LongestPage[1] < lengthOfPage:
        LongestPage = (url, lengthOfPage)
    
        with open("longest.txt", "w") as file:
            file.write(f'URL: {LongestPage[0]} --> Word count of {LongestPage[1]}\n')

def subdomainCheck(url):
    global Subdomain
    if(url.find(".uci.edu") == -1):
        return
    pattern = r'https?://(.*)\.uci\.edu'
    subdomain = re.search(pattern, url).group(1).lower()
    if subdomain == 'www':
        return
    Subdomain['https://' + subdomain + 'uci.edu'] += 1

def subdomainWrite():
    global Subdomain
    with open("subdomain.txt", "w") as file:
        string = "Number of subdomains in uci.edu: " + str(len(Subdomain)) + "\n"
        for item in sorted(Subdomain):
            string += f'{item}, {Subdomain[item]}\n'
        file.write(string)

def unique():
    global Visited
    with open("unique.txt", "w") as file:
        file.write(f'Unique Pages -> {len(Visited)}')



def commonWords():
    global Commoners
    with open("commoners.txt", "w") as file:
        string = ''
        for count, kv in enumerate(sorted(Commoners.items(), key=(lambda x: x[1]), reverse=True)[:50]):
            string += f'{count+1:02}, {kv[0]} - {kv[1]}\n'
        file.write(string)



def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global DoNotCrawl, Visited

    if url in Visited or url in DoNotCrawl:
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if parsed.netloc not in set(["ics.uci.edu/", "cs.uci.edu", "stat.uci.edu", "today.uci.edu", "informatics.uci.edu/"]):
            return False

        if parsed.netloc == "today.uci.edu" and parsed.path != "/department/information_computer_sciences/":
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

