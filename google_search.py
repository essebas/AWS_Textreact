import urllib
import requests
from bs4 import BeautifulSoup

query = "Mr.Robot"
query = query.replace(' ', '+')
URL = f"https://google.com/search?q={query}"

# Agente escritorio
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"

# Agente mobil
MOBILE_AGENT = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"

headers = {"user-agent": USER_AGENT}
response = requests.get(URL, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")


results = []
for g in soup.find_all('div', class_='rc'):
    anchors = g.find_all('a')
    if anchors:
        link = anchors[0]['href']
        title = g.find('h3').text
        content = g.find(class_ = 's').text
        item = {
            "title" : title,
            "content" : content,
            "link" : link
        }
        results.append(item)
0
print('\n'.join('{}: {}'.format(*k) for k in enumerate(results)))
