#!/usr/bin/python3

from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from progress.bar import Bar
from requests import get
import re
import csv
import os
import json
  
list_of_assembly_accessions = []
i = 0

species_tree_list_from_json = []

final_list = []
dictionary = {}

URL_ncbi = 'https://www.ncbi.nlm.nih.gov'
URL_ncbi_assembly = 'https://www.ncbi.nlm.nih.gov/assembly/'
URL_ncbi_bioproject = 'https://www.ncbi.nlm.nih.gov/bioproject/'
URL_pubmed = 'https://pubmed.ncbi.nlm.nih.gov/'

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

def read_json(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    
    for species in data:
        species_tree_list_from_json.append(species.get('Species')) if species.get('Species') not in species_tree_list_from_json else species_tree_list_from_json

    return(data)

def get_doi(bioProject_URL):

    doi_x = ''
    list_of_pubmed_id = []

    URL = URL_ncbi_bioproject+ '?term=' + bioProject_URL

    page = get(URL)
    bs = BeautifulSoup(page.content, 'html.parser')

    for element in bs.find_all('a', class_='RegularLink'):
        if (re.search('href="/pubmed', str(element))):
            list_of_pubmed_id.append(element.get('href')) if element.get('href') not in list_of_pubmed_id else list_of_pubmed_id

    for link in list_of_pubmed_id:

        URL_doi = URL_ncbi + link
            
        page_4 = get(URL_doi)
        bs_4 = BeautifulSoup(page_4.content, 'html.parser')
        doi = str(bs_4.find_all('span', class_="citation-doi"))
        doi = re.sub('<.*?>', '', doi).split(',')[0].lstrip('[').strip().rstrip('.').split()[1]
        doi_x += '{}  '.format(doi)

    return doi_x

def project_status(biosample):

    URL = 'https://gold.jgi.doe.gov/projects?setColumns=yes&Study.Relevance.ID_options=or&Project.NCBI+BioSample+Accession=' + str(biosample)
    page = get(URL)

    bs = BeautifulSoup(page.content, 'html.parser')

    try:
        project_status_info = bs.find('tr', class_='odd')
        project_status_info = str(project_status_info.find_all('td')[3])
        project_status_info = re.sub('<.*?>', '', project_status_info).strip()

        return(project_status_info)
    except:
        project_status_info = ''
        return(project_status_info)

def save_to_csv():

    with open('results1.csv', 'w', encoding='utf8', newline='') as output_file:
        fc = csv.DictWriter(output_file, fieldnames=final_list[0].keys())
        fc.writeheader()
        fc.writerows(final_list)

def get_list_of_query(json_content):

    families_of_tree = []
    for dict in json_content:
        families_of_tree.append((dict.get('Family'))) if (dict.get('Family')) not in families_of_tree else families_of_tree

    return(families_of_tree)

def find_information(element):

    list_of_results = []

    element = element.split()[0]
    
    subDirectory = "?term=" + element

    URL = URL_ncbi_assembly + subDirectory
    
    driver = webdriver.Chrome(executable_path='/home/adrian/chromedriver/stable/chromedriver', chrome_options=chrome_options)
    driver.get(URL)

    try:
        load_button1 = expected_conditions.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/form/div[1]/div[3]/div[2]/div/div[1]/ul/li[2]/a/span'))
        WebDriverWait(driver, 15).until(load_button1)

        el = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/form/div[1]/div[3]/div[2]/div/div[1]/ul/li[2]/a/span')
        webdriver.ActionChains(driver).move_to_element(el).click(el).perform()

        load_button1 = expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="ps200"]'))

        el = driver.find_element(By.XPATH, '//*[@id="ps200"]')
        webdriver.ActionChains(driver).move_to_element(el).click(el).perform()

        page = driver.page_source
    except:
        page = ''
 
    bs = BeautifulSoup(page)

    driver.close()
    driver.quit()

    for result in bs.find_all('div', class_="rprt"):
        list_of_results.append(result)
    
    return list_of_results, element

# znajduje genBank accesion code i dodaje do listy
def assign_info_to_list(find_information_results):

    list_of_results, element = find_information_results

    for result in list_of_results:
 
        genBank_assembly_accession = str(result.find_all('dl', class_="details")[7])
        genBank_assembly_accession = re.sub('<.*?>', '', genBank_assembly_accession).split()[-2]


        if genBank_assembly_accession == 'accession:':
            genBank_assembly_accession = str(result.find_all('dl', class_="details")[6])
            genBank_assembly_accession = re.sub('<.*?>', '', genBank_assembly_accession).split()[-2]

        list_of_assembly_accessions.append([genBank_assembly_accession, element])

def species_is_a_tree():
    pass

def for_genBank_code_find_info(genBank_assembly_accession):
         
    URL_2 = URL_ncbi_assembly + genBank_assembly_accession[0]

    page_2 = get(URL_2)

    bs_2 = BeautifulSoup(page_2.content, 'html.parser')

    basic_info = bs_2.find_all('dl', class_="assembly_summary_new margin_t0")
    basic_info = re.sub('<.*?>', ' ', str(basic_info)).split()

    species_name_from_ncbi = '{} {}'.format(basic_info[basic_info.index("name:") + 1], basic_info[basic_info.index("name:") + 2])
    if species_name_from_ncbi not in species_tree_list_from_json: 
        print('{} - nie ma na liście drzew!'.format(species_name_from_ncbi))
        return None

    global_statistics = bs_2.find_all('tbody')
    global_statistics = re.sub('<.*?>', ' ', str(global_statistics)).split()

    dictionary['bio_project'] = basic_info[basic_info.index("BioProject:") + 1]

    try:
        dictionary['family'] = genBank_assembly_accession[1]
    except:
        pass
    try:
        dictionary['genus'] = basic_info[basic_info.index("name:") + 1]
    except:
        pass
    try:
        dictionary['species'] = basic_info[basic_info.index("name:") + 2]
    except:
        pass
    try:
        dictionary['biosample'] = basic_info[basic_info.index("BioSample:") + 1]
    except:
        pass
    try:
        dictionary['date'] = basic_info[basic_info.index("Date:") + 1]
    except:
        pass
    try:
        dictionary['assembly_level'] = basic_info[basic_info.index("level:") + 1]
    except:
        pass
    try:
        dictionary['genome_representation'] = basic_info[basic_info.index("representation:") + 1]
    except:
        pass
    try:
        dictionary['genBank_assembly_accession'] = genBank_assembly_accession[0]
    except:
        pass
    
    # global statistics
    try:
        dictionary['Total ungapped length'] = global_statistics[global_statistics.index("ungapped") + 2]
    except:
        pass
    try:
        dictionary['Gaps between scaffolds'] = global_statistics[global_statistics.index("between") + 2]
    except:
        pass

    indexes_of = [i for i, x in enumerate(global_statistics) if x == "of"]
    for index in indexes_of:
        if global_statistics[index + 1] == 'scaffolds':
            try:
                dictionary['Number of scaffolds'] = global_statistics[index + 2]
            except:
                pass

    indexes_of = [i for i, x in enumerate(global_statistics) if x == "N50"]
    for index in indexes_of:
        if global_statistics[index - 1] == 'Scaffold':
            try:
                dictionary['Scaffold N50'] = global_statistics[index + 1]
            except:
                pass
        if global_statistics[index - 1] == 'Contig':
            try:
                dictionary['Contig N50'] = global_statistics[index + 1]
            except:
                pass
    
    indexes_of = [i for i, x in enumerate(global_statistics) if x == "L50"]
    for index in indexes_of:
        if global_statistics[index - 1] == 'Scaffold':
            try:
                dictionary['Scaffold L50'] = global_statistics[index + 1]
            except:
                pass
        if global_statistics[index - 1] == 'Contig':
            try:
                dictionary['Contig L50'] = global_statistics[index + 1]    
            except:
                pass
    try:
        dictionary['Number of contigs'] = global_statistics[global_statistics.index("contigs") + 1]
    except:
        pass
    try:
        dictionary['Total number of chromosomes and plasmids'] = global_statistics[global_statistics.index("plasmids") + 1]
    except:
        pass
    try:
        dictionary['DOI'] = get_doi(dictionary['bio_project'])
    except:
        pass
    try:
        dictionary['Project status'] = project_status(basic_info[basic_info.index("BioSample:") + 1])
    except:
        pass
    dictionary_copy = dictionary.copy()
    final_list.append(dictionary_copy)
    dictionary.clear()
    
    os.system('cls' if os.name == 'nt' else 'clear')
        

if __name__ == "__main__":

    json_file = read_json('species.json')

    os.system('cls' if os.name == 'nt' else 'clear')

    bar = Bar('', max = len(get_list_of_query(json_file)))
    for element in get_list_of_query(json_file):
        assign_info_to_list(find_information(element))
        bar.next()
    bar.finish()

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Liczba znalezionych rekordów: {}".format(len(list_of_assembly_accessions)))

    bar = Bar('', max = len(list_of_assembly_accessions))
    for genBank_assembly_accession in list_of_assembly_accessions:
        for_genBank_code_find_info(genBank_assembly_accession)
        bar.next()
    bar.finish()


    save_to_csv()

    print('Finished.')