import re
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import urldefrag
from collections import Counter
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
from bs4 import BeautifulSoup

DONOTCRAWL = set()
#part1
VISITED = set()
#part2
LONGEST_PAGE = ('Link', 0)
#part3
WORD_COUNTER = Counter()
#part4
SUBDOMAIN = Counter()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    valids = [link for link in links if is_valid(link) and link not in VISITED]
    
    # Write reports to separate files
    stat_report()
    
    return valids

def stat_report():
    write_unique_pages()
    write_longest_page()
    write_top_words()
    write_subdomains()

def write_unique_pages():
    with open('unique_pages.txt', 'w', encoding='utf-8') as f:
        f.write(f"Unique pages crawled: {len(VISITED)}\n")


def write_longest_page():
    with open('longest_page.txt', 'w', encoding='utf-8') as f:
        f.write(f"Longest page by word count:\n")
        f.write(f"URL: {LONGEST_PAGE[0]}\n")
        f.write(f"Word count: {LONGEST_PAGE[1]}\n")

def write_top_words():
    with open('top_words.txt', 'w', encoding='utf-8') as f:
        f.write("Top 50 most frequent words:\n")
        f.write("--------------------------\n")
        for word, count in WORD_COUNTER.most_common(50):
            f.write(f"{word}: {count}\n")

def write_subdomains():
    with open('subdomains.txt', 'w', encoding='utf-8') as f:
        f.write("Subdomains and their page counts:\n")
        f.write("--------------------------------\n")
        for subdomain, count in sorted(SUBDOMAIN.items()):
            f.write(f"{subdomain}: {count}\n")

def LONGEST_PAGECheck(url, lengthOfPage):
    global LONGEST_PAGE
    if LONGEST_PAGE[1] < lengthOfPage:
        LONGEST_PAGE = (url, lengthOfPage)

'''
def similar(hash1, hash2):
    count = 0
    for h1, h2 in zip(hash1, hash2):
        if h1 == h2
            count += 1
    return count / 160 #or other number depending on hash used

'''

def subdomain_update(url):
    global SUBDOMAIN
    if(".uci.edu" not in url):
        return
    pattern = r'https?://(.*)\.uci\.edu'
    subdomain_str = re.search(pattern, url).group(1).lower()                        
    if subdomain_str == 'www':
        return
    key = f'http://{subdomain_str}.uci.edu'
    SUBDOMAIN[key] += 1



def computeWordFrequencies(tokenList):
    global WORD_COUNTER
    stopWords = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "cannot", "could", "did", "do", "does",
    "doing", "down", "during", "each", "few", "for", "from", "further", "had",
    "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "let", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
    "ain", "aren", "couldn", "didn", "doesn", "don", "hadn", "hasn", "haven",
    "isn", "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren",
    "won", "wouldn", "arent", "cant", "couldnt", "didnt", "doesnt", "dont", "hadnt", "hasnt",
    "havent", "isnt", "mightnt", "mustnt", "neednt", "shant", "shouldnt",
    "wasnt", "werent", "wont", "wouldnt", "im", "ive", "youve", "youre",
    "youll", "youd", "shes", "hes", "its", "theres", "lets", "thats", "wheres",
    "whos", "whats", "hows", "whys", "also", "however", "therefore", "thus", "otherwise", "else", "perhaps",
    "maybe", "whether", "yet", "though", "although", "despite", "toward",
    "towards", "within", "without", "among", "amongst", "regarding"
    ]
    for token in tokenList:
        if token not in stopWords and token.isalpha() and len(token) > 3:
            WORD_COUNTER[token] += 1

def tokenize(resp):
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        text = soup.get_text()
        tokens = nltk.tokenize.word_tokenize(text)
        word_tokens = [t.lower() for t in tokens if re.match(r'^[a-zA-Z0-9]+$', t)]
        return word_tokens
    except AttributeError:
        return []

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    global DONOTCRAWL, VISITED
    list_of_links = set()  
    
    if resp.status != 200:
        DONOTCRAWL.add(url)
        return list_of_links 
    
    try:
        page_data = resp.raw_response.content
        html = page_data.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)

        curr_url, _ = urldefrag(url)
        parsed_curr_url = urlparse(curr_url)

        if parsed_curr_url.path != '/':
            curr_path = parsed_curr_url.path.rstrip('/')
        else:
            curr_path = parsed_curr_url.path
        
        curr_url = parsed_curr_url._replace(path=curr_path).geturl()

        if curr_url in VISITED or curr_url in DONOTCRAWL:
            return list_of_links

        VISITED.add(curr_url)

        subdomain_update(curr_url)
        tokens = tokenize(resp)
        length_of_page = len(tokens)
        if length_of_page < 200 or length_of_page > 25000:
            DONOTCRAWL.add(curr_url)
            return list_of_links
        LONGEST_PAGECheck(url, length_of_page)
        computeWordFrequencies(tokens)

        for link in links:
            full_link = urljoin(url, link['href'])
            defrag_link, _ = urldefrag(full_link)
            parsed = urlparse(defrag_link)

            netloc = parsed.netloc
            if parsed.path != '/':
                path = parsed.path.rstrip('/')
            else:
                path = parsed.path

            new_url = parsed._replace(netloc=netloc, path=path).geturl()

            if new_url not in VISITED and new_url not in DONOTCRAWL:
                list_of_links.add(new_url)

    except Exception as e:
        print(f"Failed to process {url}: {e}")
        DONOTCRAWL.add(url)
    
    return list_of_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    global DONOTCRAWL, VISITED
    try:
        url, _ = urldefrag(url)  # Remove fragment
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            DONOTCRAWL.add(url)
            return False

        if url in DONOTCRAWL or url in VISITED:
            return False

        # General traps
        trap_keywords = [
            'ical=', 'outlook-ical', 'eventdisplay=past', 'tribe-bar-date', 'action=', 'share=', 'swiki',
            'calendar', 'event', 'events', '/?page=', '/?year=', '/?month=', '/?day=', '/?view=archive',
            '/?sort=', 'sessionid=', 'utm_', 'replytocom=', '/html_oopsc/', '/risc/v063/html_oopsc/a\\d+\\.html',
            '/doku', 'doku.php', '/files/', '/papers/', '/publications/', '/pub/', 'wp-login.php', 'login.php', '?do=edit', '?do=diff','?rev=',
            '/seminarseries'
        ]
        lowered_url = url.lower()
        # If any trap keyword is found, reject the URL and add to DONOTCRAWL
        if any(keyword in lowered_url for keyword in trap_keywords):
            DONOTCRAWL.add(url)
            return False

        # More specified traps for "grape.ics.uci.edu"
        if "grape.ics.uci.edu" in parsed.netloc:
            if "/wiki/asterix/" in parsed.path:
                DONOTCRAWL.add(url)
                return False
            if "timeline" in parsed.path and "from=" in parsed.query:
                DONOTCRAWL.add(url)
                return False

        # Lost of pages with little info
        if "~eppstein" in parsed.path:
            if "pix" in parsed.path or "163" in parsed.path:
                DONOTCRAWL.add(url)
                return False            

        valid_domains = (".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu", ".today.uci.edu")
        
         # Special case for a specific path
        if parsed.netloc.endswith(".today.uci.edu") and parsed.path.startswith("/department/information_computer_sciences/"):
            return True  

        if parsed.netloc.endswith(valid_domains):
            return True

        if re.match(
            r".*\.(?:css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|apk|bak|tmp|log|db|mdb|manifest|map|lock|java|py"
            + r"|sql|img|svg|heic|webp|bam|xml|ff|png|pfd|ps\.z|pix"
            + r"|ppxs|mol|ppsx|sh)$", parsed.path.lower()):
            DONOTCRAWL.add(url)
            return False

        return False

    except TypeError:
        print("TypeError for ", url)
        raise
