
# NCBI-web-scraper

NCBI-web-scraper creates a .csv file that contains information about sequencing 
projects for selected organisms.

The data comes from the following NCBI databases:

    - assembly (www.ncbi.nlm.nih.gov/assembly),
    - bioproject (www.ncbi.nlm.nih.gov/bioproject),
    - biosample (www.ncbi.nlm.nih.gov/biosample)

and they are extended with information from the following databases:

    - JGI GOLD (gold.jgi.doe.gov),
    - PubMed (pubmed.ncbi.nlm.nih.gov).

### Information contained in the output file

- family,
- genus,
- species,
- BioSample code,
- BioProject code,
- GenBank assembly code,
- date,
- assembly level,
- genome representation,
- DOI codes of a publications,
- project status.

Global statistics

- Total ungapped length,
- Gaps between scaffolds,
- Number of scaffolds,
- Scaffold N50,
- Contig N50,
- Scaffold L50,
- Contig L50,
- Number of contigs,
- Total number of chromosomes and plasmids.





## Installation

Necessary packages.

```bash
  pip install selenium
  pip install beautifulsoup4
  pip install progress
  pip install requests
```
    
To run the main.py script, you need a Chrome browser with an additional webdriver file
corresponding to the browser version.

https://www.google.com/intl/pl_pl/chrome

https://chromedriver.chromium.org/downloads

**The CHROME_DRIVER_PATH variable should contain the path to the chromedriver.**

```python
 CHROME_DRIVER_PATH = '/chromedriver/path' # 26 code line
```

## NCBI-web-scrapper workflow

#### **get_species.py**
get_species.py gets taxonomic data of tree species found at 
https://en.wikipedia.org/wiki/List_of_trees_and_shrubs_by_taxonomic_family

#### **species.json**
The data collected by the get_species.py script is saved in the species.json file and contains a list of dictionaries 
with information about the species name and family.
This file is used by the main.py script to collect data about these organisms.

In order to gather information on the sequencing projects of the organisms of 
interest to us, edit the species.json file in the same way, or create your own. 
The English name of the family or the common name of the species is not taken 
into account by the script.

```json
[{"Species": "Citrus sinensis", "Family": "Rutaceae"}]
```

#### **main.py**
main.py uses the family name (key 'Family') from the file 'species.json' as 
the search term in the NCBI assembly database. Organism data is searched and 
saved only if the found species is found in the file species.json (key 'Species'). 
This solution reduces the number of script queries.