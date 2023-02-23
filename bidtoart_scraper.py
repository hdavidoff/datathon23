import pandas as pd
import requests
import os
from bs4 import BeautifulSoup
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
opts = Options()
opts.headless = True
assert opts.headless  # Operating in headless mode
browser = Firefox(options=opts)

def remove_accents(artist):
    accents = ['é', 'è', 'ê', 'à', 'á', 'ó', 'ö']
    replacement = ['e', 'e', 'e', 'a', 'a', 'o', 'o']
    for i, accent in enumerate(accents):
        artist = artist.replace(accent, replacement[i])
    return artist

def remove_extras(artist):
    extras = ['(after)', '(studio of)', '(inspired by)', 'Van Delft', 'Leiden', 'Sir', 
              'Von', '(Titian)', 'The Younger', '(Robusti)', 'R.W.S.', '(Monsu, Desiderio)', 
              "de'", 'the Elder']
    for extra in extras:
        artist = artist.replace(extra, '').strip()
    return artist

def get_url_addon(artist):
    artist = remove_accents(artist)
    artist = remove_extras(artist)
    artist = artist.replace('-', ' ')
    if ',' in artist:
        artist = artist.replace(',','').strip()
        url_addon = '%20'.join(artist.lower().split(' ')[::-1])
    else:
        url_addon = '%20'.join(artist.lower().split(' '))
    return url_addon

def get_url_addon_2(artist):
    artist = artist.lower().split(' ')[0]+' '+artist.lower().split(' ')[-1]
    artist = artist.replace('(','')
    artist = artist.replace(')','')
    return get_url_addon(artist)

def get_number_auction_results(artist_url):
    text = requests.get(artist_url).text
    try:
        snippet = text.split("total_lot_items:")[1].split(',')[0]
        return int(snippet)
    except:
        return 0
        
def get_links_from_url(url):
    links = []
    browser.get(url)
    elems = browser.find_elements('xpath', "//a[@href]")
    for elem in elems:
        links.append(elem.get_attribute("href"))
    links = [link for link in links if "https" in link]
    return links
    
def get_links_to_artist(artist_name):
    url_addon = get_url_addon(artist_name)
    url = f"https://bidtoart.com/advanced-search?filter=artist&name={artist}"
    links = get_links_from_url(url)
    links = [link for link in links if "/artist/" in link]
    if len(links) == 0:
        url_addon = get_url_addon(artist_name)
        url = f"https://bidtoart.com/advanced-search?filter=artist&name={url_addon}"
        links = get_links_from_url(url)
        links = [link for link in links if "/artist/" in link]
    return list(set(links))

def get_links_to_artworks(artist_url):
    first_letters_artist = artist_url.split('/')[4][:5]
    all_links = []
    number_artworks = get_number_auction_results(artist_url)
    number_pages = -(-number_artworks // 20) #Website displays 20 results per page
    if number_pages > 10: number_pages = 10 #Stops looking after 200th painting to save time
    for i in range(number_pages):
        url_addon = f"?tab=results&sortBy=price.desc&pageIndex={i+1}"
        page_links = get_links_from_url(artist_url + url_addon)
        all_links += [link for link in page_links if f"/art/{first_letters_artist}" in link]
    return list(set(all_links))

def get_artwork_info(artwork_url):
    page = requests.get(artwork_url)
    table = BeautifulSoup(page.text, "html.parser").find("table")
    table_data = [tr.text for tr in table.find_all("tr")]
    data_dict = dict([data.replace('\n', '').split(':', 1) for data in table_data])
    return data_dict

artworks_df = pd.read_csv("FilesCSVFormat/Artwork.csv")
artists_df = pd.read_csv("FilesCSVFormat/Artist.csv")
artist_id_dict = dict(pd.Series(artists_df.name.values,index=artists_df.id).to_dict())
artists_list = set(list(artists_df.name))
artworks_df["artist_name"] = [artist_id_dict[artist_id] for artist_id in artworks_df["artist"]]

if "bidtoart_prices.csv" in os.listdir():
    prices_df = pd.read_csv("bidtoart_prices.csv")
else:
    prices_df = pd.DataFrame(columns=["url", "name", "original_artist", "scraped_artist", 
                                      "estimate", "medium", "size (HxWxD)", "date", "auction date"])

artists_not_found = []
artists_done = set(list(prices_df.original_artist))
artists_to_do = list(artists_list - artists_done - set(artists_not_found))

for artist in artists_to_do:
    i = 0
    print(artist)
    artist_urls = get_links_to_artist(artist)
    for artist_url in artist_urls:
        artwork_urls = get_links_to_artworks(artist_url)
        print(f"artworks in link: {len(artwork_urls)}")
        for artwork_url in artwork_urls:
            i += 1
            data = get_artwork_info(artwork_url)
            df_row = [artwork_url, data.get("Artwork title"), artist, 
                      data.get("Artist"), data.get("Estimate"), 
                      data.get("Medium"),data.get("Size (HxWxD)"), 
                      data.get("Date of painting"), data.get("Auction date")]
            prices_df.loc[len(prices_df.index)] = df_row
        prices_df.to_csv("bidtoart_prices.csv", index=None)
    if i == 0:
        artists_not_found.append(artist)
    print("Artists not found below, add to script in future reruns to avoid wasting time")
    print("_______________________________________________________")
    print(artists_not_found)
    print("_______________________________________________________")