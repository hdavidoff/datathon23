import pandas as pd

conversion = {'$': 1, 'A$': 0.69, 'CA$': 0.74, 'CHF': 1.08, 'DKK': 0.14, 'HK$': 0.13, 
              'SEK': 0.1, '£': 1.2, '¥': 0.01, '€': 1.07, 'HUF': 0.00279, 'SGD\xa0': 0.75, 
              'NOK\xa0': 0.1, 'MX$': 0.05, 'PLN': 0.22, 'ZAR\xa0': 0.06, 'NZ$': 0.62, 
              'CN¥': 0.15, 'MAD': 0.012, 'CZK': 0.05, 'EGP': 0.03, 'GRD': 0.0031, 'VEF': 4e-07, 
              'INR': 0.012, 'RUB': 0.014, '₹': 0.012, 'R$': 0.19, 'FIM\xa0': 0.18, 'QAR\xa0': 0.27, 
              'IEP': 1.26, 'RON': 0.2, 'ESP': 0.0064, 'UAH': 0.027, 'TL': 0.053, 'EEK': 0.0717, 
              'SKK': 0.045, 'FJD\xa0': 0.46, 'CAD': 0.74, 'MXN': 0.054, 'AUD': 0.69, 'CNY': 0.15, 
              'HKD': 0.13, 'COP': 0.0002, 'TWD': 0.033, 'kr': 0.1, 'PHP': 0.18, 'NZD': 0.62, 
              'R': 0.055, 'CHF\xa0': 1.08, 'DKK\xa0': 0.14, 'SEK\xa0': 0.1, 'HUF\xa0': 0.00279, 
              'PLN\xa0': 0.22, 'CZK\xa0': 0.05, 'EGP\xa0': 0.03, 'GRD\xa0': 0.0031, 'VEF\xa0': 4e-07, 
              'RUB\xa0': 0.014, 'IEP\xa0': 1.26, 'RON\xa0': 0.2, 'ESP\xa0': 0.0059, 'UAH\xa0': 0.027, 
              'EEK\xa0': 0.0717, 'SKK\xa0': 0.045, 'USD': 1, 'GBP': 1.2, 'NLG': 0.48, 'EUR': 1.07, 
              'ITL': 0.00057, 'BEF': 0.026, 'FRF': 0.16, 'DEM': 0.54, 'SGD': 0.75}


def convert_estimate(estimate):
    v1, v2 = estimate.replace(',','').split('-')
    v1, v2 = v1.strip(' '), v2.strip(' ')
    unit = ''.join([i for i in v1 if not i.isdigit()])
    if unit not in conversion.keys():
        print(v1)
        print(f"Add unit {unit} to conversion dictionary")
        return
    else:
        value1 = int(''.join([i for i in v1 if i.isdigit()]))*conversion[unit]
        try:
            value2 = int(''.join([i for i in v2 if i.isdigit()]))*conversion[unit]
            return (value1+value2)/2
        except:
            return value1

def convert_price(price):
    unit, value = price.split(' ')
    value = int(value.replace(',',''))
    if unit not in conversion.keys():
        print(f"Add unit {unit} to conversion dictionary")
    else:
        return value*conversion[unit]

## Findartinfo is already in dollars

## Bidtoart
bidtoart_df = pd.read_csv("bidtoart_english.csv")
bidtoart_df['price'] = [convert_estimate(est) for est in list(bidtoart_df.estimate)]

## Christies
christies_df = pd.read_csv("christies_english.csv")
indices = christies_df[christies_df["priceUSD"].isna()].index.values.astype(int)
for index in indices:
    try:
        christies_df.at[index, 'priceUSD'] = convert_price(christies_df.at[index, 'price'])
    except:
        pass
christies_df.to_csv("christies_english.csv", index=None)

## Invaluable
# Here artist names are often found in title and can be removed
invaluable_df = pd.read_csv("invaluable_english.csv")

indices = invaluable_df[invaluable_df["price"].isna()].index.values.astype(int)
for index in indices:
    try:
        invaluable_df.at[index, 'price'] = convert_price(invaluable_df.at[index, 'estimate'])
    except:
        pass

def clean_string(string):
    string = str(string).lower()
    string = remove_accents(string)
    chars = ['(', ')', '-', ',', '.',':',';']
    for char in chars:
        string = string.replace(char,'')
    return string

def remove_accents(string):
    accents = ['é', 'è', 'ê', 'à', 'á', 'ó', 'ö']
    replacement = ['e', 'e', 'e', 'a', 'a', 'o', 'o']
    for i, accent in enumerate(accents):
        string = string.replace(accent, replacement[i])
    return string

indices = invaluable_df.index.values.astype(int)
for index in indices:
    words_in_name = str(invaluable_df.at[index, 'artist']).split(' ')
    for word in words_in_name:
        invaluable_df.at[index, 'name'] = str(invaluable_df.at[index, 'name']).replace(word,'').strip()
        invaluable_df.at[index, 'name_english'] = str(invaluable_df.at[index, 'name_english']).replace(word,'').strip()
        
invaluable_df.to_csv("invaluable_english.csv")