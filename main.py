#!/usr/bin/python3

import time
import json
import re
import csv
import os
from contextlib import suppress
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from progress.bar import ShadyBar
from requests import get

list_of_assembly_accessions = []
species_tree_list_from_json = []
final_list = []

URL_NCBI = 'https://www.ncbi.nlm.nih.gov'
URL_NCBI_ASSEMBLY = 'https://www.ncbi.nlm.nih.gov/assembly/'
URL_NCBI_BIOPROJECT = 'https://www.ncbi.nlm.nih.gov/bioproject/'
URL_GOLD = 'https://gold.jgi.doe.gov/'
CHROME_DRIVER_PATH = '/home/adrian/chromedriver/stable/chromedriver'

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

def read_json(file_path):
    '''Returns the content of the json file.'''
    with open(file_path, "r", encoding="utf8") as file:
        data = json.load(file)
    for species in data:
        species_tree_list_from_json.append(species.get('Species')) if species.get('Species') \
            not in species_tree_list_from_json else species_tree_list_from_json

    return data


def clear_terminal():
    '''Clears the terminal.'''
    os.system('cls' if os.name == 'nt' else 'clear')


def get_doi(bio_project_link):
    '''
    Returns a string containing all PubMed publication "DOI" numbers that relate to BioProject data.
    '''
    doi_string = ''
    list_of_pubmed_id = []
    url = URL_NCBI_BIOPROJECT + bio_project_link

    page = get(url)
    bs = BeautifulSoup(page.content, 'xml')

    for link in bs.find_all('a', class_='RegularLink'):
        if re.search('href="/pubmed', str(link)):
            list_of_pubmed_id.append(link.get('href')) if link.get('href') \
                not in list_of_pubmed_id else list_of_pubmed_id

    for pubmed_id in list_of_pubmed_id:
        url_doi = URL_NCBI + pubmed_id
        page_doi = get(url_doi)
        bs2 = BeautifulSoup(page_doi.content, 'html.parser')
        doi = str(bs2.find_all('span', class_="citation-doi"))
        doi = re.sub('<.*?>', '', doi).split(',')[0].lstrip('[').strip().rstrip('.').split()[1]
        doi_string += '{}  '.format(doi)

    return doi_string


def project_status(biosample):
    '''
    Based on the BioSample number, the function retrieves
    information from the online genome database 'JGI GOLD'
    and returns the status of the sequencing project.
    '''
    path = 'projects?setColumns=yes&Study.Relevance.ID_options=or&Project.NCBI+BioSample+Accession='
    url = URL_GOLD + path + str(biosample)

    page = get(url)
    bs = BeautifulSoup(page.content, 'html.parser')

    try:
        project_status_info = bs.find('tr', class_='odd')
        project_status_info = str(project_status_info.find_all('td')[3])
        project_status_info = re.sub('<.*?>', '', project_status_info).strip()
        return project_status_info
    except:
        project_status_info = ''
        return project_status_info


def save_to_csv():
    '''Saves the results to the results.csv file.'''
    try:
        with open('results.csv', 'w', encoding='utf8', newline='') as output_file:
            fc = csv.DictWriter(output_file, fieldnames = final_list[0].keys())
            fc.writeheader()
            fc.writerows(final_list)
            print(f'\nSaved {len(final_list)} records in "results.csv" file.')
    except IndexError:
        print('No species was found!\n')


def get_list_of_query(json_content):
    '''The function returns a list of species families from the contents of the .json file.'''
    families_of_tree = []
    for record in json_content:
        families_of_tree.append((record.get('Family'))) if (record.get('Family')) \
            not in families_of_tree else families_of_tree

    return families_of_tree


def find_information(element):
    '''
    The function for its argument returns all search results
    in the NCBI assembly database along with its argument.
    '''
    list_of_results = []
    element = element.split()[0]
    sub_dir = "?term=" + element
    url = URL_NCBI_ASSEMBLY + sub_dir

    driver = webdriver.Chrome(executable_path = CHROME_DRIVER_PATH, \
        options = chrome_options)
    driver.get(url)

    # Changes from 20 to 200 search results displayed per page, if a button is available.
    try:
        load_button1 = expected_conditions.presence_of_element_located((By.XPATH, \
            '/html/body/div[1]/div[1]/form/div[1]/div[3]/div[2]/div/div[1]/ul/li[2]/a/span'))
        WebDriverWait(driver, 15).until(load_button1)

        el = driver.find_element(By.XPATH, \
            '/html/body/div[1]/div[1]/form/div[1]/div[3]/div[2]/div/div[1]/ul/li[2]/a/span')

        webdriver.ActionChains(driver).move_to_element(el).click(el).perform()
        load_button1 = expected_conditions.presence_of_element_located((By.XPATH, \
            '//*[@id="ps200"]'))

        el = driver.find_element(By.XPATH, '//*[@id="ps200"]')
        webdriver.ActionChains(driver).move_to_element(el).click(el).perform()

        page = driver.page_source
    except:
        page = driver.page_source

    bs = BeautifulSoup(page, "html.parser")
    driver.close()
    driver.quit()

    for result in bs.find_all('div', class_="rprt"):
        list_of_results.append(result)

    return list_of_results, element


def assign_info_to_list(find_information_results):
    '''
    The function adds information to the 'list_of_assembly_accessions'
    with the GenBank assembly accession code and the name of the species family.

    This information will be used to find information on each project.
    '''
    list_of_results, element = find_information_results

    for result in list_of_results:
        genbank_assembly_access = str(result.find_all('dl', class_="details")[7])
        genbank_assembly_access = re.sub('<.*?>', '', genbank_assembly_access).split()[-2]

        if genbank_assembly_access == 'accession:':
            genbank_assembly_access = str(result.find_all('dl', class_="details")[6])
            genbank_assembly_access = re.sub('<.*?>', '', genbank_assembly_access).split()[-2]

        list_of_assembly_accessions.append([genbank_assembly_access, element])


def for_genBank_code_find_info(genbank_assembly_access):
    '''
    The function adds a dictionary with information from the databases:
    - NCBI assembly, 
    - PubMed, 
    - JGI GOLD
    about the project specified in the function argument to the 'final_list'.
    '''
    dictionary = {}
    url = URL_NCBI_ASSEMBLY + genbank_assembly_access[0]
    page = get(url)
    bs = BeautifulSoup(page.content, 'html.parser')
    basic_info = bs.find_all('dl', class_="assembly_summary_new margin_t0")
    basic_info = re.sub('<.*?>', ' ', str(basic_info)).split()

    # Checks whether a given species is on the list of species that interest us.
    try:
        species_name_from_ncbi = '{} {}'.format(basic_info[basic_info.index("name:") + 1], basic_info[basic_info.index("name:") + 2])
        if species_name_from_ncbi not in species_tree_list_from_json:
            return None
    except:
        pass

    global_statistics = bs.find_all('tbody')
    global_statistics = re.sub('<.*?>', ' ', str(global_statistics)).split()

    try:
        dictionary['bio_project'] = basic_info[basic_info.index("BioProject:") + 1]
    except:
        return None

    with suppress(ValueError): dictionary['family'] = genbank_assembly_access[1]
    with suppress(ValueError): dictionary['genus'] = basic_info[basic_info.index("name:") + 1]
    with suppress(ValueError): dictionary['species'] = basic_info[basic_info.index("name:") + 2]
    with suppress(ValueError): dictionary['biosample'] = basic_info[basic_info.index("BioSample:") + 1]
    with suppress(ValueError): dictionary['date'] = basic_info[basic_info.index("Date:") + 1]
    with suppress(ValueError): dictionary['assembly_level'] = basic_info[basic_info.index("level:") + 1]
    with suppress(ValueError): dictionary['genome_representation'] = basic_info[basic_info.index("representation:") + 1]
    with suppress(ValueError): dictionary['genbank_assembly_access'] = genbank_assembly_access[0]
    with suppress(ValueError): dictionary['Total ungapped length'] = global_statistics[global_statistics.index("ungapped") + 2]
    with suppress(ValueError): dictionary['Gaps between scaffolds'] = global_statistics[global_statistics.index("between") + 2]


    indexes_of = [i for i, x in enumerate(global_statistics) if x == "of"]
    for index in indexes_of:
        if global_statistics[index + 1] == 'scaffolds':
            dictionary['Number of scaffolds'] = global_statistics[index + 2]

    indexes_of = [i for i, x in enumerate(global_statistics) if x == "N50"]
    for index in indexes_of:

        if global_statistics[index - 1] == 'Scaffold':
            dictionary['Scaffold N50'] = global_statistics[index + 1]

        if global_statistics[index - 1] == 'Contig':
            dictionary['Contig N50'] = global_statistics[index + 1]

    indexes_of = [i for i, x in enumerate(global_statistics) if x == "L50"]
    for index in indexes_of:
        if global_statistics[index - 1] == 'Scaffold':
            dictionary['Scaffold L50'] = global_statistics[index + 1]

        if global_statistics[index - 1] == 'Contig':
            dictionary['Contig L50'] = global_statistics[index + 1]

    with suppress(ValueError): dictionary['Number of contigs'] = global_statistics[global_statistics.index("contigs") + 1]
    with suppress(ValueError): dictionary['Total number of chromosomes and plasmids'] = global_statistics[global_statistics.index("plasmids") + 1]
    with suppress(ValueError): dictionary['DOI'] = get_doi(dictionary['bio_project'])
    with suppress(ValueError): dictionary['Project status'] = project_status(basic_info[basic_info.index("BioSample:") + 1])

    dictionary_copy = dictionary.copy()
    final_list.append(dictionary_copy)


def main():
    json_file = read_json('species.json')
    start = time.time()

    clear_terminal()

    print('Retrieving information of each tree family:\n')

    progress_bar = ShadyBar('', max = len(get_list_of_query(json_file)))
    for query in get_list_of_query(json_file):
        assign_info_to_list(find_information(query))
        progress_bar.next()
    progress_bar.finish()

    print('\nRetrieval of species information:\n')

    progress_bar = ShadyBar('', max = len(list_of_assembly_accessions))
    for genbank_assembly_access in list_of_assembly_accessions:
        for_genBank_code_find_info(genbank_assembly_access)
        progress_bar.next()
    progress_bar.finish()

    save_to_csv()

    end = time.time()
    execution_time = round(end - start, 1)

    print(f'\nScript execution time: {execution_time} s.\n')
    print('Finished.')


if __name__ == "__main__":
    main()
