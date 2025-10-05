#!/usr/bin/env python3
"""
Real-time Wikipedia Taxonomy Extractor for Species Tree Service
Visits https://en.wikipedia.org/wiki/Template:Taxonomy/{genus} in real-time
to extract complete taxonomic information for any species.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote
from typing import List, Dict, Optional
from app.models.taxonomy import TaxonomicRank, TaxonomyResponse, TaxonomicTuple, TaxonomyTuplesResponse

class TaxonomyExtractor:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_genus_from_scientific_name(self, scientific_name: str) -> str:
        """Extract genus (first part) from scientific name"""
        if ' ' in scientific_name:
            return scientific_name.split()[0]
        return scientific_name
    
    def visit_taxonomy_template(self, genus: str) -> Optional[BeautifulSoup]:
        """Visit the Template:Taxonomy/{genus} page in real-time"""
        try:
            template_url = f"Template:Taxonomy/{genus}"
            full_url = f"{self.base_url}{quote(template_url)}"
            
            print(f"🌐 Visiting: {full_url}")
            
            response = self.session.get(full_url, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                print(f"❌ HTTP Error {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error accessing page: {e}")
            return None
    
    def extract_ancestral_taxa(self, soup: BeautifulSoup) -> List[TaxonomicRank]:
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
                                
                                ancestral_taxa.append(TaxonomicRank(
                                    rank=rank_clean,
                                    name=name_text,
                                    link=link if link else None
                                ))
                        
                        break  # Found the ancestral taxa table
            
            return ancestral_taxa
            
        except Exception as e:
            print(f"❌ Error extracting ancestral taxa: {e}")
            return []
    
    def clean_rank_text(self, rank_text: str) -> str:
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
    
    def extract_taxonomy_realtime(self, scientific_name: str) -> Optional[TaxonomyResponse]:
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
        result = TaxonomyResponse(
            input_scientific_name=scientific_name,
            genus=genus,
            source_url=f'https://en.wikipedia.org/wiki/Template:Taxonomy/{genus}',
            ancestral_taxa=ancestral_taxa,
            total_taxa_found=len(ancestral_taxa),
            extraction_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            extraction_method='real-time'
        )
        
        return result
    
    def extract_as_tuples(self, scientific_name: str) -> Optional[TaxonomyTuplesResponse]:
        """Extract taxonomy and return as parent-child tuples"""
        taxonomy_data = self.extract_taxonomy_realtime(scientific_name)
        
        if not taxonomy_data:
            return None
        
        tuples = []
        ancestral_taxa = taxonomy_data.ancestral_taxa
        
        # Create tuples from the hierarchical data
        for i in range(len(ancestral_taxa) - 1):
            parent = ancestral_taxa[i]
            child = ancestral_taxa[i + 1]
            
            tuples.append(TaxonomicTuple(
                parent_taxon=parent.name,
                has_child=True,
                child_taxon=child.name
            ))
        
        # Add the final taxon (species) as a child of the last parent
        if ancestral_taxa:
            last_parent = ancestral_taxa[-1]
            tuples.append(TaxonomicTuple(
                parent_taxon=last_parent.name,
                has_child=True,
                child_taxon=scientific_name
            ))
        
        return TaxonomyTuplesResponse(
            scientific_name=scientific_name,
            tuples=tuples,
            total_relationships=len(tuples),
            extraction_method='real-time'
        )