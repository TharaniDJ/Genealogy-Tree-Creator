 #!/usr/bin/env python3
"""
Real-time Wikipedia Taxonomy Extractor
Visits https://en.wikipedia.org/wiki/Template:Taxonomy/{genus} in real-time
to extract complete taxonomic information for any species.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote

class RealTimeTaxonomyExtractor:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_genus_from_scientific_name(self, scientific_name):
        """Extract genus (first part) from scientific name"""
        if ' ' in scientific_name:
            return scientific_name.split()[0]
        return scientific_name
    
    def visit_taxonomy_template(self, genus):
        """Visit the Template:Taxonomy/{genus} page in real-time"""
        try:
            template_url = f"Template:Taxonomy/{genus}"
            full_url = f"{self.base_url}{quote(template_url)}"
            
            print(f"🌐 Visiting: {full_url}")
            
            response = self.session.get(full_url)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                print(f"❌ HTTP Error {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error accessing page: {e}")
            return None
    
    def extract_ancestral_taxa(self, soup):
        """Extract ancestral taxa from the taxonomy template page"""
        ancestral_taxa = []
        
        try:
            # Look for the table with "Ancestral taxa" header
            tables = soup.find_all('table', class_=['infobox', 'biota'])
            
            for table in tables:
                # Check if this table contains ancestral taxa
                header_row = table.find('tr')
                if header_row:
                    header_text = header_row.get_text(strip=True)
                    if 'Ancestral taxa' in header_text:
                        print("✅ Found Ancestral taxa table")
                        
                        # Process all rows in this table
                        rows = table.find_all('tr', class_='taxonrow')
                        print(f"📋 Processing {len(rows)} taxonomy rows...")
                        
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                # First cell contains rank, second contains taxon name
                                rank_cell = cells[0]
                                name_cell = cells[1]
                                
                                rank_text = rank_cell.get_text(strip=True).replace(':', '')
                                name_text = name_cell.get_text(strip=True)
                                
                                # Skip empty rows or "...." rows
                                if not rank_text or not name_text or rank_text == '.....' or name_text == '.....':
                                    continue
                                
                                # Extract link if available
                                link = ''
                                link_elem = name_cell.find('a')
                                if link_elem and link_elem.get('href'):
                                    link = f"https://en.wikipedia.org{link_elem.get('href')}"
                                
                                # Clean up rank text (remove formatting indicators)
                                rank_clean = self.clean_rank_text(rank_text)
                                
                                ancestral_taxa.append({
                                    'rank': rank_clean,
                                    'name': name_text,
                                    'link': link
                                })
                        
                        break  # Found the ancestral taxa table
            
            return ancestral_taxa
            
        except Exception as e:
            print(f"❌ Error extracting ancestral taxa: {e}")
            return []
    
    def clean_rank_text(self, rank_text):
        """Clean up rank text by removing formatting"""
        # Remove common formatting
        rank_clean = rank_text.replace('Clade:', 'Clade').strip()
        if rank_clean.endswith(':'):
            rank_clean = rank_clean[:-1]
        
        # Remove HTML tags
        rank_clean = rank_clean.replace('<i>', '').replace('</i>', '')
        rank_clean = rank_clean.replace('<b>', '').replace('</b>', '')
        
        # Handle "Clade" specially
        if 'Clade' in rank_clean and rank_clean != 'Clade':
            rank_clean = 'Clade'
        
        return rank_clean
    
    def extract_taxonomy_realtime(self, scientific_name):
        """Main method to extract taxonomy in real-time"""
        print(f"🔬 Starting real-time taxonomy extraction for: {scientific_name}")
        
        # Extract genus
        genus = self.extract_genus_from_scientific_name(scientific_name)
        print(f"🧬 Extracted genus: {genus}")
        
        # Visit the taxonomy template page
        soup = self.visit_taxonomy_template(genus)
        if not soup:
            return None
        
        # Extract ancestral taxa
        ancestral_taxa = self.extract_ancestral_taxa(soup)
        
        if not ancestral_taxa:
            print("❌ No ancestral taxa found")
            return None
        
        print(f"✅ Successfully extracted {len(ancestral_taxa)} taxonomic entries")
        
        # Create result
        result = {
            'input_scientific_name': scientific_name,
            'genus': genus,
            'source_url': f'https://en.wikipedia.org/wiki/Template:Taxonomy/{genus}',
            'ancestral_taxa': ancestral_taxa,
            'total_taxa_found': len(ancestral_taxa),
            'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'extraction_method': 'real-time'
        }
        
        return result
    
    def extract_to_csv_format(self, scientific_name):
        """Extract taxonomy and format as CSV row similar to test dataset"""
        result = self.extract_taxonomy_realtime(scientific_name)
        
        if not result:
            return None
        
        # Initialize CSV row with all taxonomic ranks
        csv_row = {
            'domain': '', 'kingdom': '', 'subkingdom': '', 'superphylum': '',
            'phylum': '', 'subphylum': '', 'superclass': '', 'class': '', 'subclass': '',
            'infraclass': '', 'superorder': '', 'order': '', 'suborder': '', 'infraorder': '',
            'parvorder': '', 'superfamily': '', 'family': '', 'subfamily': '', 'tribe': '',
            'subtribe': '', 'genus': '', 'subgenus': '', 'species': '', 'subspecies': '',
            'variety': '', 'form': '', 'morph': '', 'strain': '', 'Animal Name': scientific_name
        }
        
        # Map extracted taxa to CSV format
        for taxon in result['ancestral_taxa']:
            rank = taxon['rank'].lower()
            name = taxon['name']
            
            # Map rank names to CSV column names
            if rank in csv_row:
                csv_row[rank] = name
            elif rank == 'clade':
                # Handle clades - try to map to appropriate rank based on context
                continue
        
        # Add the species name to genus and species fields
        if ' ' in scientific_name:
            genus_name, species_name = scientific_name.split(' ', 1)
            csv_row['genus'] = genus_name
            csv_row['species'] = scientific_name
        
        return csv_row
    
    def create_dataset_from_species_list(self, species_list, output_file='extracted_taxonomy_dataset.csv'):
        """Create a CSV dataset from a list of species names"""
        import pandas as pd
        
        print(f"🔬 Creating taxonomy dataset for {len(species_list)} species...")
        
        all_rows = []
        successful_extractions = 0
        
        for i, species in enumerate(species_list, 1):
            print(f"\n[{i}/{len(species_list)}] Processing: {species}")
            
            try:
                csv_row = self.extract_to_csv_format(species)
                if csv_row:
                    all_rows.append(csv_row)
                    successful_extractions += 1
                    print(f"   ✅ Success")
                else:
                    print(f"   ❌ Failed to extract data")
                    
                # Add delay to be respectful to Wikipedia
                time.sleep(1)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        if all_rows:
            # Create DataFrame and save to CSV
            df = pd.DataFrame(all_rows)
            df.to_csv(output_file, index=False)
            
            print(f"\n🎉 Dataset created successfully!")
            print(f"   📁 File: {output_file}")
            print(f"   📊 Total species: {len(species_list)}")
            print(f"   ✅ Successful extractions: {successful_extractions}")
            print(f"   ❌ Failed extractions: {len(species_list) - successful_extractions}")
            print(f"   📈 Success rate: {(successful_extractions/len(species_list)*100):.1f}%")
            
            return df
        else:
            print("❌ No successful extractions - dataset not created")
            return None

if __name__ == "__main__":

    extractor = RealTimeTaxonomyExtractor()

    # Sample species list for dataset creation
    sample_species = [
        'Homo sapiens',
        'Panthera leo', 
        'Panthera tigris',
        'Canis lupus',
        'Felis catus',
        'Elephas maximus',
        'Loxodonta africana', 
        'Gorilla gorilla',
        'Pan troglodytes',
        'Bos taurus',
        'Sus scrofa',
        'Equus caballus',
        'Gallus gallus',
        'Anas platyrhynchos',
        'Salmo salar',
        'Drosophila melanogaster'
    ]
    
    print("🧬 Taxonomy Dataset Generator")
    print("=" * 50)
    print("Choose an option:")
    print("1. Extract single species")
    print("2. Create dataset from sample species")
    print("3. Create dataset from custom species list")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # Single species extraction
        scientific_name = input("Enter scientific name: ").strip() or 'Homo sapiens'
        try:
            result = extractor.extract_taxonomy_realtime(scientific_name)
            if result:
                print(f"\n📊 Extracted {len(result['ancestral_taxa'])} taxonomic levels:")
                for taxon in result['ancestral_taxa']:
                    print(f"   {taxon['rank']}: {taxon['name']}")
                    
                # Also show CSV format
                csv_row = extractor.extract_to_csv_format(scientific_name)
                if csv_row:
                    print(f"\n📄 CSV Format Preview:")
                    for rank, name in csv_row.items():
                        if name:  # Only show non-empty fields
                            print(f"   {rank}: {name}")
        except Exception as e:
            print(f"❌ Error processing {scientific_name}: {e}")
            
    elif choice == "2":
        # Create dataset from sample species
        print(f"\n🔬 Creating dataset from {len(sample_species)} sample species...")
        dataset = extractor.create_dataset_from_species_list(sample_species, 'sample_taxonomy_dataset.csv')
        
    elif choice == "3":
        # Custom species list
        print("\nEnter species names (one per line, empty line to finish):")
        custom_species = []
        while True:
            species = input().strip()
            if not species:
                break
            custom_species.append(species)
        
        if custom_species:
            filename = input("Enter output filename (default: custom_taxonomy_dataset.csv): ").strip()
            if not filename:
                filename = 'custom_taxonomy_dataset.csv'
            
            dataset = extractor.create_dataset_from_species_list(custom_species, filename)
        else:
            print("No species provided.")
    
    else:
        print("Invalid choice. Running default single species extraction...")
        result = extractor.extract_taxonomy_realtime('Homo sapiens')
        print(result['ancestral_taxa'])
    
