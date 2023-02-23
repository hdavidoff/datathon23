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
import time
import math

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

def sort_titles(str_list):
    splitted = [string.split('\n') for string in str_list]
    artists = [item[0] for item in splitted]
    titles = []
    for item in splitted:
        if len(item) == 2:
            titles.append(item[1])
        else:
            titles.append(None)
    return titles, artists

def sort_prices(str_list):
    realised = [item.split('\n')[1] for item in str_list[1::2]]
    estimate = []
    for item in [item.split('\n') for item in str_list[0::2]]:
        if len(item) == 2:
            estimate.append(item[1])
        else:
            estimate.append(None)
    return realised, estimate

def get_number_items(url_addon, browser):
    url = f"https://www.christies.com/search?entry={url_addon}&page=1&sortby=realized_desc&tab=sold_lots#main-content"
    browser.get(url)
    browser.maximize_window()
    i = 1
    while True:
        try:
            time.sleep(i)
            available, sold = [int(elem.text[1:-1]) for elem in browser.find_elements('xpath', '//div/button/span')[1:4:2]]
            return sold
        except:
            i += 1
            print("failed loading, trying again")
            browser.refresh()
            browser.get(url)
            if i > 3:
                return 0

def get_page_data(page_url, browser):
    browser.get(page_url)
    browser.maximize_window()
    i = 1
    while True:
        try:
            time.sleep(i)
            prices_check = [elem.text for elem in browser.find_elements('class name', "chr-lot-tile__dynamic-price")]
            prices_length = len([i for i in prices_check if len(i)>1])
            if prices_length == 0:
                return {"name":[], "price":[], "estimate":[], "artist_name":[]}
            #titles = [elem.text for elem in browser.find_elements('class name', "chr-lot-tile__secondary-title ellipsis--one-line")]
            titles, artists = sort_titles([elem.text for elem in browser.find_elements('class name', "chr-lot-tile__titles")])
            realised, estimate = sort_prices([elem.text for elem in browser.find_elements('class name', "chr-lot-tile__price-container")])
            data_dict = {"name":titles[:prices_length], "price":realised[:prices_length], 
                         "estimate":estimate[:prices_length], "artist_name":artists[:prices_length]}
            if len(data_dict["name"])>1:
                return data_dict
        except:
            i += 1
            print("failed, trying again")
            browser.refresh()
            browser.get(page_url)

def get_artist_data(artist, browser):
    url_addon = get_url_addon(artist)
    number_sold_lots = get_number_items(url_addon, browser)
    if number_sold_lots == 0:
        url_addon = get_url_addon_2(artist)
        number_sold_lots = get_number_items(url_addon, browser)
        if number_sold_lots == 0: print(f"{artist} needs to be checked manually")
    items_per_page = 20
    number_pages = int(math.ceil(number_sold_lots/items_per_page))
    if number_pages > 10: number_pages = 10
    data_dict = get_page_data(f"https://www.christies.com/search?entry={url_addon}&page={1}&sortby=realized_desc&tab=sold_lots#main-content", browser)
    for page in range(1, number_pages):
        url = f"https://www.christies.com/search?entry={url_addon}&page={page+1}&sortby=realized_desc&tab=sold_lots#main-content"
        new_data_dict = get_page_data(url, browser)
        data_dict = {key:data_dict[key]+new_data_dict[key] for key in data_dict.keys()}
    return data_dict

artists_not_found = ["Continental School", "Italian School", "French School", "Istvan Csok", "Rodrigo de Villandrando", 
                         "Theofilos (Hadjimichail)", "Tivadar Kosztka Csontváry", "Teodor Axentowicz", "Carl Gutherz", 
                         "Dr. H.A. Oldfield", "Hans Olaf Heyerdahl", "Otto Greiner", "Albert Lambron Des Pilitieres",
                         "Melozzo da Forli", "Edgar Melville Ward", "H. Pittard", "Agost Benkhard", "Grafton Tyler Brown",
                         "Simone Peterzano", "Thure de Thulstrup", "Auguste Joseph Marie De Mersseman", "Zdzislaw Piotr Jasinski",
                         "Aby Altson", "Theobald Reinhold von Oer", "Giorgio da Castelfranco Veneto", "Saturnino Herran", 
                         "Emile Signol", "Marquise de Brehan", "Henry Alexander Bowler", "Christian F. Schwerdt",
                         "Federico de Madrazo y Kuntz", "Franz Xaver Messerschmidt", "Collier Twentyman Smithers", 
                         "Victor Tortez", "Tullio Garbari"]

if "christies_prices.csv" in os.listdir():
    prices_df = pd.read_csv("christies_prices.csv")
else:
    prices_df = pd.DataFrame(columns=["name", "price", "estimate", "artist_name"])

artists_df = pd.read_csv("FilesCSVFormat/Artist.csv")
artists_list = set(list(artists_df.name))

artists_done = set(list(prices_df.artist))
artists_to_do = list(artists_list - artists_done - set(artists_not_found))

browser = Firefox(options=opts)
for artist_name in artists_to_do:
    print(artist_name)
    data_dict = get_artist_data(artist_name, browser)
    df = pd.DataFrame.from_dict(data_dict)
    df["artist"] = artist_name
    prices_df = pd.concat([prices_df, df])
    print(f"artworks found: {len(df)}")
    prices_df.to_csv("christies_prices.csv", index=None)
    browser.delete_all_cookies()
    print("Artists not found below, add to script in future reruns to avoid wasting time")
    print("_______________________________________________________")
    print(artists_not_found)
    print("_______________________________________________________")