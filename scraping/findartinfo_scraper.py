import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

def remove_accents(artist):
    accents = ['é', 'è', 'ê', 'à', 'á', 'ó', 'ö']
    replacement = ['e', 'e', 'e', 'a', 'a', 'o', 'o']
    for i, accent in enumerate(accents):
        artist = artist.replace(accent, replacement[i])
    return artist

def remove_extras(artist):
    extras = ['(after)', '(studio of)', '(inspired by)', 'Van Delft', 'Leiden', 'Sir', 'Von', '(Titian)', 'The Younger', '(Robusti)']
    for extra in extras:
        artist = artist.replace(extra, '').strip()
    return artist

def split_names_line(str_list):
    names = []
    sizes = []
    for string in str_list:
        i = 0
        while not string[i].isdigit():
            i += 1
        names.append(string[:i])
        sizes.append(string[i:])
    return names, sizes

def get_page_data(page):
    table = BeautifulSoup(page.text, "html.parser").find_all("table")[1]
    table_data = [tr.text for tr in table.find_all("tr")][0]
    splitted = [line for line in table_data.replace('\n', '').replace('  ', '').split('\r') if not line.isspace()]
    splitted = [line for line in splitted if line]
    dates = splitted[8:-2:4]
    names, sizes = split_names_line(splitted[9:-2:4])
    media = splitted[10:-2:4]
    prices = [int(string.replace('USD', '').replace(',','')) for string in splitted[11:-2:4] if "Unsold" not in string]
    data_dict = {"name":names[:len(prices)], "price":prices, "medium":media[:len(prices)], 
                 "auction_date":dates[:len(prices)], "size":sizes[:len(prices)]}
    return data_dict

def get_artist_data(artist_url):
    page = requests.get(artist_url)
    data_dict = get_page_data(page)
    number_pages = int(page.text.split("Page")[1].split(" of ")[1].split("(max")[0].strip())
    for n in range(1, number_pages):
        url = artist_url.replace("/1.html", f"/{n+1}.html")
        page = requests.get(url)
        new_data_dict = get_page_data(page)
        data_dict = {key:data_dict[key]+new_data_dict[key] for key in data_dict.keys()}
        if data_dict["price"][-1] < 10000:
            break
    return data_dict

def get_artist_urls(artist):
    artist_original = artist
    artist = remove_accents(artist)
    artist = remove_extras(artist)
    artist = artist.replace('-', ' ')
    print(artist)
    if ',' in artist:
        artist = artist.replace(',','').strip()
        url_addon = '+'.join(artist.lower().split(' ')[::-1])
    else:
        url_addon = '+'.join(artist.lower().split(' '))
    url = f"https://findartinfo.com/english/Artists/Result?artistName={url_addon}"
    page = requests.get(url)
    links = [text.split('"')[0] for text in page.text.split('href="') if text[0]=='/']
    links = list(set([link for link in links if "/english/list-prices-by-artist" in link]))
    links = [link.replace("by-artist/", "by-artist/4/") for link in links]
    links = [f"https://findartinfo.com{link[:-5]}/page/1.html" for link in links]
    if len(links)==0 and len(artist.lower().split(' ')) != 2:
            artist = artist.lower().split(' ')[0]+' '+artist.lower().split(' ')[-1]
            links = get_artist_urls(artist)
    return links

artists_not_found = ['Walter Frier', 'Bernardo Bellotto (Canaletto)', 'Andre Henri Dargelas', 'Samuel Page', 
                              'William Shakespeare Burton', 'Rene Avigdor', 'P. Joos van Gent and Berruguete', 
                              'Peter Maverick', 'Giotto Di Bondone', 'Bunsei', 'and Snyders, F. Rubens, Peter Paul',
                              'Rosa Jameson', 'Agost Benkhard', 'Gherardo Di Jacopo Starnina', 'Albert Lambron Des Pilitieres',
                              'Christian F. Schwerdt', 'Cosme Tura', 'Dr. H.A. Oldfield', 'Francesco Del Cossa',
                              'Marquise de Brehan', 'Melozzo da Forli', 'Istvan Csok', 'Russian Unknown Master',
                              'Sevillian School', 'H. Pittard', 'Johannes Becx', 'Pieter II Peetersz', 'Franz Xaver Messerschmidt',
                              'Tivadar Kosztka Csontváry']
artists_df = pd.read_csv("FilesCSVFormat/Artist.csv")
artists_list = set(list(artists_df.name))
if "findartinfo_prices.csv" in os.listdir():
    prices_df = pd.read_csv("findartinfo_prices.csv")
else:
    prices_df = pd.DataFrame(columns=["name", "price", "medium", "auction_date", "size", "artist"])
artists_done = set(list(prices_df.artist))
artists_to_do = list(artists_list - artists_done - set(artists_not_found))

for artist in artists_to_do:
    print(artist)
    artist_urls = get_artist_urls(artist)
    for artist_url in artist_urls:
        data_dict = get_artist_data(artist_url)
        df = pd.DataFrame.from_dict(data_dict)
        df["artist"] = artist
        prices_df = pd.concat([prices_df, df])
        print(f"artworks in link: {len(df)}")
    print("Artists not found below, add to script in future reruns to avoid wasting time")
    print("_______________________________________________________")
    print(artists_not_found)
    print("_______________________________________________________")
    prices_df.to_csv("findartinfo_prices.csv", index=None)