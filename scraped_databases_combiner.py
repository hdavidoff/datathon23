import pandas as pd
from collections import Counter

###
###
### Importing the data ###
###
###
# Import the given artworks and artists
# The artworks_english database was made by adding the extra column "name_english" unsing the translator notebook
artworks_df = pd.read_csv("artworks_english.csv") 
artists_df = pd.read_csv("FilesCSVFormat/Artist.csv")
artist_id_dict = dict(pd.Series(artists_df.name.values,index=artists_df.id).to_dict())
artists_list = list(artists_df.name)
artworks_df["artist_name"] = [artist_id_dict[artist_id] for artist_id in artworks_df["artist"]]
artworks_df["price"] = None
artworks_df["price_name"] = None

# All databases were translated and prices/estimates converted to dollar
findartinfo_df = pd.read_csv("findartinfo_english.csv")
christies_df = pd.read_csv("christies_english.csv")
christies_df["price_original"] = christies_df.price
christies_df.price = christies_df.priceUSD
del christies_df['priceUSD']
bidtoart_df = pd.read_csv("bidtoart_english.csv")
bidtoart_df.rename(columns={'original_artist':'artist'}, inplace=True)
invaluable_df = pd.read_csv("invaluable_english.csv")

# Combine all databases and do some cleaning up
final_df = pd.concat([findartinfo_df, christies_df, bidtoart_df, invaluable_df], ignore_index=True)
final_df.dropna(subset=['price'], inplace=True)
final_df.drop_duplicates(subset=['name','artist'], keep='first')
final_df.sort_values(by='price', ascending=False, inplace=True)
final_df.reset_index(drop=True, inplace=True)
final_df.to_csv("scraped_artworks.csv", index=None)

###
###
### Matching the titles ###
###
###
#look for most common words in titles to avoid matching them
all_words = ' '.join(list(artworks_df.name)).lower().split(' ')
cnt = Counter()
for word in all_words:
    cnt[word] += 1
skip_words = set([i[0] for i in list(cnt.most_common(20))])

def strip_title(title): 
    # This removes punctuation from titles
    title = str(title).lower()
    chars = ['(', ')', '-', ',', '.',':',';']
    for char in chars:
        title = title.replace(char,'')
    return title

def check_best_from_indices(indices): 
    # If two titles match, take the most expensive 
    # (logic is that the artworks in artwork.csv tend to be the most expensive for each artist)
    price_max = 0
    index_max = indices[0]
    for index in indices:
        price = final_df.at[index, 'price']
        if price > price_max:
            price_max = price
            index_max = index
    return index_max

def get_scraped_title_sets(artist):
    # This separates the title into a word set, usable for set operations
    # Indices to the original title are also returned
    indices = list(final_df[final_df["artist"] == artist].index.values.astype(int))
    word_sets = list()
    for i in indices:
        words = strip_title(final_df.name.iloc[i]).split(' ')
        words_english = strip_title(final_df.name_english.iloc[i]).split(' ')
        word_sets.append(set(words) & set(words_english) - skip_words)
    return indices, word_sets

def match_titles(artist):
    # Matching algorithm:
    # 1. Get cleaned word sets of title and translated title for both paintings in the original database and scraped database
    # 2. Calculate overlap (number of common words) between word sets, and select artwork from scraped database with the highest overlap
    # 3. If multiple matches are found, select most expensive
    # 4. Update original artwork database with new prices and names of the 
    indices_given_artworks = artworks_df[artworks_df["artist_name"] == artist].index.values.astype(int)
    indices_scraped_artworks, scraped_word_sets = get_scraped_title_sets(artist)
    for i in indices_given_artworks:
        max_overlap = 0
        overlap_indices = []
        words = strip_title(artworks_df.name.iloc[i]).split(' ')
        words_english = strip_title(artworks_df.name_english.iloc[i]).split(' ')
        all_words = set(words) & set(words_english) - skip_words
        for j in range(len(indices_scraped_artworks)):
            overlap = len(scraped_word_sets[j] & all_words)
            if overlap == max_overlap:
                overlap_indices.append(indices_scraped_artworks[j])
            elif overlap > max_overlap:
                max_overlap = overlap
                overlap_indices = [indices_scraped_artworks[j]]
        if max_overlap > 0:
            best_index = check_best_from_indices(overlap_indices)
            artworks_df.at[i, 'price'] = final_df.at[best_index, 'price']
            artworks_df.at[i, 'price_name'] = final_df.at[best_index, 'name']

for artist in artists_list:
    match_titles(artist)
    
###
###
### Interpolating leftover prices ###
###
###
def interpolate_artworks():
    # Get the average artwork price for each artist
    price_per_artist = dict()
    for artist in artists_list:
        prices = list(artworks_df[artworks_df.artist_name==artist][artworks_df.price>500].price)
        if len(prices) == 0:
            average_price = 0
        else:
            average_price = sum(prices)/len(prices)
        price_per_artist[artist] = average_price

    # Update database
    for artist in price_per_artist.keys():
        if price_per_artist[artist] > 500:
            indices_nan_prices = artworks_df[artworks_df["artist_name"] == artist][artworks_df["price"].isna()].index.values.astype(int)
            indices_low_prices = artworks_df[artworks_df["artist_name"] == artist][artworks_df["price"] < 500].index.values.astype(int)
            for index in list(indices_nan_prices)+list(indices_low_prices):
                artworks_df.at[index, 'price'] = price_per_artist[artist]
                artworks_df.at[index, 'price_name'] = "average price of artist"

interpolate_artworks()
interpolate_artworks() #Repeat a second time

###
###
### Saving final database ###
###
###
artworks_df.to_csv("artworks_with_prices_v3.csv", index=None)