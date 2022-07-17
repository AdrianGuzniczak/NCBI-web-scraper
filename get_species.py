#!/usr/bin/python3

import re
import json
from bs4 import BeautifulSoup
from requests import get

species_list = []

def find_species():
    '''
    The function retrieves information about organisms from
    https://en.wikipedia.org/wiki/List_of_trees_and_shrubs_by_taxonomic_family
    '''
    url = 'https://en.wikipedia.org/wiki/List_of_trees_and_shrubs_by_taxonomic_family'
    page = get(url)

    bs = BeautifulSoup(page.content, 'html.parser')
    tree_classes = bs.find_all("div", {"style" : "background: white; border: 1px solid rgb(153, 153, 153); padding: 1em; width: 80%;"})

    for one_class in tree_classes:
        tree_records = one_class.find('tbody')
        tree_records = tree_records.find_all('tr')

        for one_record in tree_records:
            one_record = re.sub('<.*?>', '', str(one_record))

            if (len(one_record.split('\n')) > 3) and one_record.split('\n')[1] != 'Scientific name':

                species_dict = {}

                species_dict['Species'] = one_record.split('\n')[1]
                species_dict['Common name'] = one_record.split('\n')[3]
                species_dict['Family'] = one_record.split('\n')[5]

                species_dict_copy = species_dict.copy()
                species_list.append(species_dict_copy)

    print(f'Number of tree species found: {len(species_list)}')


def save_to_json():
    '''Saves the results to the species.json file.'''
    with open('species.json', 'w', encoding="utf8") as file:
        json.dump(species_list , file)
        print('Saved in "species.json" file.')

if __name__ == '__main__':
    find_species()
    save_to_json()
