import re
from urllib.parse import urlparse
from urllib.parse import urljoin
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')


DoNotCrawl = set()
Visited = set()
Commoners = dict()
Subdomain = dict()
LongestPage = ('Link', 0)

def commonWordsWrite():
    #global Commoners
    with open("commoners.txt", "w") as file:
        string = ''
        for count, kv in enumerate(sorted(Commoners.items(), key=(lambda x: x[1]), reverse=True)[:50]):
            string += f'{count+1:02}, {kv[0]} - {kv[1]}\n'
        file.write(string)

def longestPageWrite():
    #global LongestPage
    with open("longest.txt", "w") as file:
        file.write(f'URL: {LongestPage[0]} --> Word count of {LongestPage[1]}\n')

def subdomainWrite():
    #global Subdomain
    with open("subdomain_list.txt", "w") as f:
        file_string = 'Number of Subdomains (in uci.edu): ' + str(len(Subdomain)) + "\n"
        for kv in sorted(Subdomain):
            file_string += f'{kv}, {Subdomain[kv]}\n'
        f.write(file_string)

def subdomain_update(url):
    global Subdomain
    if(".uci.edu" not in url):
        return
    pattern = r'https?://(.*)\.uci\.edu'
    subdomain_str = re.search(pattern, url).group(1).lower()                        
    if subdomain_str == 'www':
        return 

    key = 'http://' + subdomain_str + '.uci.edu'
    if key in Subdomain:
        Subdomain[key] += 1
    else:
        Subdomain[key] = 1


def uniqueWrite():
    #global Visited
    with open("unique.txt", "w") as file:
        file.write(f'Unique Pages -> {len(Visited)}')

def scraper(url, resp):
    #global DoNotCrawl
    links = extract_next_links(url, resp)
    valids = [link for link in links if is_valid(link)] #list of valid links

    if resp.status == 200 and url not in DoNotCrawl:
        word_token_list = tokenize(resp)       
        check_longest_page(url, len(word_token_list))   
        computeWordFrequencies(word_token_list)

        commonWordsWrite()
        longestPageWrite()
        subdomainWrite()
        uniqueWrite()

    return valids



def tokenize(resp):
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
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

def check_longest_page(url, lengthOfPage):
    global LongestPage
    if LongestPage[1] < lengthOfPage:
        LongestPage = (url, lengthOfPage)

def computeWordFrequencies(tokenList):
    global Commoners
    stopWords = [
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren", "t", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn", "did", "didn", "do", "does", "doesn", "doing", "don", "down", "during", "each", "few", "for", "from", "further", "had", "hadn", "has", "hasn", "have", "haven", "having", "he", "d", "ll", "s", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "m", "ve", "if", "in", "into", "is", "isn", "it", "its", "itself", "let", "me", "more", "most", "mustn", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan", "she", "should", "shouldn", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "re", "ve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn", "we", "were", "weren", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "won", "would", "wouldn", "you", "your", "yours", "yourself", "yourselves"
    ]
    for token in tokenList:
        if token not in stopWords and token.isalpha():
            if token not in Commoners:
                Commoners[token] = 1
            else:
                Commoners[token] += 1

def extract_next_links(url, resp):
    global DoNotCrawl, Visited

    if resp.status != 200 or url in DoNotCrawl or url in Visited or resp.raw_response == None:
        DoNotCrawl.add(url)
        return set()

    Visited.add(url)

    subdomain_update(url)

    # url parser

    if wordcount_check(resp):
        DoNotCrawl.add(url)
        return set()

    list_of_links = set()
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    links = soup.find_all('a', href=True)    

    for link in links:
        href = link.get('href')

        if urlparse(url).netloc:
            href = urljoin(url, href)

        href = href.split('#')[0]

        if is_valid(href):
            list_of_links.add(href)
    return list_of_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    global DoNotCrawl, Visited
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if parsed.netloc not in set(["www.ics.uci.edu/", "www.cs.uci.edu", "www.stat.uci.edu", "www.today.uci.edu", "www.informatics.uci.edu/"]):
            return False

        if parsed.netloc == "www.today.uci.edu" and parsed.path != "/department/information_computer_sciences/":
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

def wordcount_check(resp):
    word_tokens = tokenize(resp)
    if len(word_tokens) < 150 or len(word_tokens) > 7500:
        return True
    return False