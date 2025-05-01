import re
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import urldefrag
import nltk
import gc

nltk.download('punkt')
nltk.download('punkt_tab')

from bs4 import BeautifulSoup

DoNotCrawl = set()
Visited = set()
Commoners = dict()
Subdomain = dict()
LongestPage = ('Link', 0)

trap_keywords = [
    'ical=', 'outlook-ical', 'eventdisplay=past', 'tribe-bar-date', 'action=', 'share=', 'swiki',
    'calendar', 'event', 'events', '/?page=', '/?year=', '/?month=', '/?day=', '/?view=archive',
    '/?sort=', 'sessionid=', 'utm_', 'replytocom=', '/html_oopsc/', '/risc/v063/html_oopsc/a\\d+\\.html',
    '/doku', '/files/', '/papers/', '/publications/', '/pub/', 'wp-login.php', '?do=edit', '?do=diff','?rev=',
    '/~eppstein/', '/covid19/' , '/doku', 'seminar-series', 'doku.php', 'seminarseries' , 'department-seminars',
    '/Nanda', '/seminar'
    ]
stopWords = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
    "any", "are", "aren", "t", "as", "at", "be", "because", "been", "before", "being", 
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn", "did", "didn", 
    "do", "does", "doesn", "doing", "don", "down", "during", "each", "few", "for", "from", "further", "had", 
    "hadn", "has", "hasn", "have", "haven", "having", "he", "d", "ll", "s", "her", "here", "hers", "herself", 
    "him", "himself", "his", "how", "i", "m", "ve", "if", "in", "into", "is", "isn", "it", "its", "itself", 
    "let", "me", "more", "most", "mustn", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan", 
    "she", "should", "shouldn", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "these", "they", "re", "ve", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "wasn", "we", "were", "weren", "what", "when", "where", "which", 
    "while", "who", "whom", "why", "with", "won", "would", "wouldn", "you", "your", "yours", "yourself", "yourselves"
]

def scraper(url, resp):
    global DoNotCrawl
    links = extract_next_links(url, resp)
    valids = [link for link in links if is_valid(link)] #list of valid links

    if resp.status == 200 and url not in DoNotCrawl:
        word_token_list = tokenize(resp)       
        longestPageCheck(url, len(word_token_list))   
        computeWordFrequencies(word_token_list)

    commonWordsWrite()
    longestPageWrite()
    subdomainWrite()
    uniqueWrite()

    return valids

def commonWordsWrite(): #writes the 50 most common words along with their word counts
    global Commoners
    with open("commoners.txt", "w") as file:
        string = ''
        for count, item in enumerate(sorted(Commoners.items(), key=(lambda x: x[1]), reverse=True)[:50]):
            string += f'{count+1}, {item[0]} --> {item[1]}\n'
        file.write(string)

def longestPageCheck(url, lengthOfPage): #checks if url is the new longest page
    global LongestPage
    if LongestPage[1] < lengthOfPage:
        LongestPage = (url, lengthOfPage)

def longestPageWrite(): #writes longest page's url and token count to a file
    global LongestPage
    with open("longest.txt", "w") as file:
        file.write(f'URL: {LongestPage[0]} --> Word count of {LongestPage[1]}\n')

'''
def similar(hash1, hash2):
    count = 0
    for h1, h2 in zip(hash1, hash2):
        if h1 == h2
            count += 1
    return count / 160 #or other number depending on hash used

'''

def subdomainUpdate(url): #updates whenever a subdomain is visited
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

def subdomainWrite(): #writes subdomains visited to a file
    #global Subdomain
    with open("subdomain_list.txt", "w") as file:
        string = 'Number of Subdomains (in uci.edu): ' + str(len(Subdomain)) + "\n"
        for item in sorted(Subdomain):
            string += f'{item}, {Subdomain[item]}\n'
        file.write(string)

def uniqueWrite(): #writes the amount of unique urls visited to a file
    #global Visited
    with open("unique.txt", "w") as file:
        file.write(f'Unique Pages -> {len(Visited)}')

def tokenize(resp): #tokenizer function, ignores anything that is not alphanumeric
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        text = soup.get_text()
        tokens = nltk.tokenize.word_tokenize(text)
        word_tokens = [t.lower() for t in tokens if re.match(r'^[a-zA-Z0-9]+$', t)]
        return word_tokens
    except AttributeError:
        return []

def computeWordFrequencies(tokenList): #counts the common words --> useful for the common word file
    global Commoners
    for token in tokenList:
        if token not in stopWords and token.isalpha():
            if token not in Commoners:
                Commoners[token] = 1
            else:
                Commoners[token] += 1

def wordCountCheck(resp): #check if the given site has too little or too much information
    tokens = tokenize(resp)
    return len(tokens) < 200 or len(tokens) > 75000

def extract_next_links(url, resp):
    if resp.status != 200 or resp.raw_response is None:
        print(f"[!] Skipping {url} — Bad status or no response: {resp.status}")
        DoNotCrawl.add(url)
        return set()

    content_type = resp.raw_response.headers.get('Content-Type', '').lower()

    # Bail out immediately if not HTML before reading content
    if 'text/html' not in content_type:
        print(f"[!] Skipping {url} — Non-HTML content: {content_type}")
        DoNotCrawl.add(url)
        return set()

    if url in Visited:
        print(f"[i] Already visited {url}")
        return set()

    try:
        html = resp.raw_response.content.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"[!] Decode failed for {url}: {e}")
        DoNotCrawl.add(url)
        return set()

    Visited.add(url)
    subdomainUpdate(url)
    found_links = set()

    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all('a', href=True):
            full_url = urljoin(url, tag['href'])
            href = tag['href']
            if not any(domain in href for domain in ("ics.uci.edu", "cs.uci.edu", "stat.uci.edu", "informatics.uci.edu")):
                continue
            if is_valid(full_url):
                found_links.add(full_url)
    except Exception as e:
        print(f"[!] BS4 error on {url}: {e}")
    finally: #memory management
        del html
        del soup
        gc.collect()

    return found_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    global DoNotCrawl, Visited
    try:
        parsed = urlparse(url)
        url, _ = urldefrag(url)
        base = parsed.netloc
        domain_parts = base.lower().split(".")
        base_domain = ".".join(domain_parts[-3:]) if len(domain_parts) >= 3 else base.lower()

        if parsed.scheme not in set(["http", "https"]):
            return False

        if url in DoNotCrawl or url in Visited:
            return False

        lowered_url = url.lower()
        # If any trap keyword is found, reject the URL and add to DONOTCRAWL
        if any(keyword in lowered_url for keyword in trap_keywords):
            DoNotCrawl.add(url)
            return False

        allowed_domains = {
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu"
        }

        if base == "www.today.uci.edu" and parsed.path.startswith("/department/information_computer_sciences/"):
            return True

        if base_domain not in allowed_domains:
            DoNotCrawl.add(url)
            return False

        if not base.endswith("uci.edu"): #if url is outside of domain
            return False

        if "grape.ics.uci.edu" in base or "swiki.ics.uci.edu" in base or "wics.ics.uci.edu" in base or "ngs.ics.uci.edu" in base or 'cert.ics.uci.edu' in base:
            DoNotCrawl.add(url)
            return False
        
        if len(url) > 300:
            DoNotCrawl.add(url)
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|img"
            + r"|png|tiff?|mid|mp2|mp3|mp4|txt"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|"
            + r"|thmx|mso|arff|rtf|jar|csv|sql|apk|java|xml|c|war"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
