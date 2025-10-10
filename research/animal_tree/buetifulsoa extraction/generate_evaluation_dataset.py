#!/usr/bin/env python3
"""
Dataset Generation Script for Taxonomy Extraction Evaluation
Uses the test.csv animal names to generate extracted taxonomy data for accuracy evaluation.
"""

import pandas as pd
import os
import sys
import json
import time
from datetime import datetime

# Add the current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the RealTimeTaxonomyExtractor
from taxonomy_extractor_by_gene import RealTimeTaxonomyExtractor

class DatasetGenerator:
    def __init__(self, test_csv_path, output_dir=""):
        self.test_csv_path = test_csv_path
        self.output_dir = output_dir
        self.extractor = RealTimeTaxonomyExtractor()

        
        # Load the test dataset
        self.test_df = pd.read_csv(test_csv_path)
        print(f"📊 Loaded test dataset with {len(self.test_df)} animals")
        
        # Get unique animal names
        self.animal_names = self.test_df['Animal Name'].unique()
        print(f"🐾 Found {len(self.animal_names)} unique animals to extract")
        
    def extract_taxonomy_for_animal(self, animal_name):
        """Extract taxonomy for a single animal"""
        try:
            print(f"\n🔬 Extracting taxonomy for: {animal_name}")
            
            # Use the extractor to get taxonomy
            result = self.extractor.extract_taxonomy_realtime(animal_name)
            
            if result:
                print(f"✅ Successfully extracted {result['total_taxa_found']} taxa")
                return {
                    'animal_name': animal_name,
                    'extraction_success': True,
                    'extraction_result': result,
                    'extraction_timestamp': datetime.now().isoformat()
                }
            else:
                print(f"❌ Failed to extract taxonomy")
                return {
                    'animal_name': animal_name,
                    'extraction_success': False,
                    'extraction_result': None,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'error': 'No taxonomy data found'
                }
                
        except Exception as e:
            print(f"❌ Error extracting taxonomy for {animal_name}: {e}")
            return {
                'animal_name': animal_name,
                'extraction_success': False,
                'extraction_result': None,
                'extraction_timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def generate_extracted_dataset(self, max_animals=None, delay_seconds=1):
        """Generate the extracted dataset for all animals"""
        
        animals_to_process = self.animal_names
        if max_animals:
            animals_to_process = animals_to_process[:max_animals]
            print(f"🎯 Processing first {max_animals} animals for testing")
        
        extracted_data = []
        successful_extractions = 0
        failed_extractions = 0
        
        print(f"\n🚀 Starting taxonomy extraction for {len(animals_to_process)} animals")
        print(f"⏱️ Using {delay_seconds}s delay between requests")
        
        for i, animal_name in enumerate(animals_to_process, 1):
            print(f"\n[{i}/{len(animals_to_process)}] Processing: {animal_name}")
            
            # Extract taxonomy
            extraction_result = self.extract_taxonomy_for_animal(animal_name)
            extracted_data.append(extraction_result)
            
            # Update counters
            if extraction_result['extraction_success']:
                successful_extractions += 1
            else:
                failed_extractions += 1
            
            # Progress update
            if i % 10 == 0:
                success_rate = (successful_extractions / i) * 100
                print(f"\n📈 Progress: {i}/{len(animals_to_process)} ({i/len(animals_to_process)*100:.1f}%)")
                print(f"   Success rate: {success_rate:.1f}% ({successful_extractions}/{i})")
                print(f"   Failed: {failed_extractions}")
            
            # Delay to be respectful to Wikipedia
            if i < len(animals_to_process):  # Don't delay after the last item
                time.sleep(delay_seconds)
        
        # # Save the extracted data
        # output_file = os.path.join(self.output_dir, f"extracted_taxonomy_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        # with open(output_file, 'w', encoding='utf-8') as f:
        #     json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Extraction Complete!")
        # print(f"📁 Saved to: {output_file}")
        print(f"📊 Summary:")
        print(f"   Total animals processed: {len(animals_to_process)}")
        print(f"   Successful extractions: {successful_extractions}")
        print(f"   Failed extractions: {failed_extractions}")
        print(f"   Success rate: {(successful_extractions/len(animals_to_process)*100):.1f}%")
        
        return extracted_data
    
    def convert_to_csv_format(self, extracted_data):
        """Convert extracted data to CSV format similar to test.csv"""
        
        print(f"\n📋 Converting extracted data to CSV format...")
        
        # Define the taxonomic ranks in order
        rank_columns = [
            'domain', 'kingdom', 'subkingdom', 'superphylum', 'phylum', 'subphylum',
            'superclass', 'class', 'subclass', 'infraclass', 'superorder', 'order',
            'suborder', 'infraorder', 'parvorder', 'superfamily', 'family', 'subfamily',
            'tribe', 'subtribe', 'genus', 'subgenus', 'species', 'subspecies',
            'variety', 'form', 'morph', 'strain'
        ]
        
        csv_data = []
        
        for extraction in extracted_data:
            if not extraction['extraction_success']:
                continue
                
            animal_name = extraction['animal_name']
            ancestral_taxa = extraction['extraction_result']['ancestral_taxa']
            
            # Create a row with empty values
            row = {col: '' for col in rank_columns}
            row['Animal Name'] = animal_name
            
            # Fill in the taxonomic data
            for taxon in ancestral_taxa:
                rank = taxon['rank'].lower()
                name = taxon['name']
                
                # Map rank variations to standard names
                rank_mapping = {
                    'clade': 'clade',  # Keep as is, will be handled specially
                    'superkingdom': 'kingdom',
                    'infraorder': 'infraorder',
                    'parvorder': 'parvorder'
                }
                
                mapped_rank = rank_mapping.get(rank, rank)
                
                # Handle clade specially (might map to various levels)
                if rank == 'clade':
                    # Skip clades for now, or you could implement logic to map them appropriately
                    continue
                
                if mapped_rank in rank_columns:
                    row[mapped_rank] = name
            
            csv_data.append(row)
        
        # Create DataFrame
        extracted_df = pd.DataFrame(csv_data)
        
        # Save to CSV
        csv_output_file = os.path.join(self.output_dir, f"result.csv")
        extracted_df.to_csv(csv_output_file, index=False)
        
        print(f"✅ CSV format saved to: {csv_output_file}")
        print(f"📊 Extracted CSV has {len(extracted_df)} rows and {len(extracted_df.columns)} columns")
        
        return csv_output_file, extracted_df

def main():
    """Main function to run the dataset generation"""
    
    # Configuration
    test_csv_path = "test.csv"  # Path to your test dataset (in same directory)
    max_animals_for_testing = 100# Set to None for all animals, or a number for testing
    delay_between_requests = 2  # seconds
    
    print("🧬 TAXONOMY EXTRACTION DATASET GENERATOR")
    print("=" * 50)
    
    # Check if test.csv exists
    if not os.path.exists(test_csv_path):
        print(f"❌ Test dataset not found: {test_csv_path}")
        print("Please make sure test.csv is in the current directory")
        return
    
    # Initialize generator
    generator = DatasetGenerator(test_csv_path)
    
    # Generate extracted dataset
    extracted_data = generator.generate_extracted_dataset(
        max_animals=max_animals_for_testing,
        delay_seconds=delay_between_requests
    )
    
    # Convert to CSV format for easy comparison
    csv_output_file, extracted_df = generator.convert_to_csv_format(extracted_data)
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"2. Compare with ground truth using: {csv_output_file}")
    print(f"3. Run evaluation metrics in the Jupyter notebook")
    print(f"4. Adjust max_animals_for_testing={max_animals_for_testing} as needed")

if __name__ == "__main__":
    main()