import { PersonData } from '@/lib/types';

export interface ProcessRelationshipsParams {
  relationships: any[];
  personalDetails: Record<string, PersonData>;
  searchQuery: string;
  addFamilyRelationWrapper: (
    parent: string,
    parentGender: 'father' | 'mother',
    child: string,
    parentGen: number,
    childGen: number,
    spouse?: string
  ) => void;
}

export const processRelationships = ({
  relationships,
  personalDetails,
  searchQuery,
  addFamilyRelationWrapper,
}: ProcessRelationshipsParams) => {

  // Group relationships by type
  const childParentRels: { child: string, parent: string }[] = [];
  const spouseRels: { person1: string, person2: string }[] = [];
  
  relationships.forEach((rel) => {
    const { entity1, relationship, entity2 } = rel;
    
    if (relationship === 'child of') {
      childParentRels.push({ child: entity1, parent: entity2 });
    } else if (relationship === 'spouse of') {
      spouseRels.push({ person1: entity1, person2: entity2 });
    }
  });
  
  // Get all unique people from relationships
  const allPeople = new Set<string>();
  childParentRels.forEach(({ child, parent }) => {
    allPeople.add(child);
    allPeople.add(parent);
  });
  spouseRels.forEach(({ person1, person2 }) => {
    allPeople.add(person1);
    allPeople.add(person2);
  });
  
  // Check if we have personal details for all people involved
  const allPeopleArray = Array.from(allPeople);
  const missingPersonalDetails = allPeopleArray.filter(person => !personalDetails[person]);
  
  if (missingPersonalDetails.length > 0) {
    console.log('Waiting for personal details for:', missingPersonalDetails);
    return false; // Return false to indicate processing should wait
  }
  
  console.log('All personal details received, processing relationships...');
  
  // Create a map to track spouses for each person
  const spouseMap = new Map<string, string>();
  spouseRels.forEach(({ person1, person2 }) => {
    spouseMap.set(person1, person2);
    spouseMap.set(person2, person1);
  });
  
  // Simple generation assignment logic
  const personGenerations = new Map<string, number>();
  
  // Step 1: Set the search query person as generation 0 (starting point)
  personGenerations.set(searchQuery, 0);
  
  // Step 2: Keep iterating until all generations are assigned
  let changed = true;
  let iterations = 0;
  const maxIterations = 10; // Prevent infinite loops
  
  while (changed && iterations < maxIterations) {
    changed = false;
    iterations++;
    
    // Process parent-child relationships
    childParentRels.forEach(({ child, parent }) => {
      if (personGenerations.has(parent) && !personGenerations.has(child)) {
        // Child is one generation higher than parent
        personGenerations.set(child, personGenerations.get(parent)! + 1);
        changed = true;
      } else if (personGenerations.has(child) && !personGenerations.has(parent)) {
        // Parent is one generation lower than child
        personGenerations.set(parent, personGenerations.get(child)! - 1);
        changed = true;
      }
    });
    
    // Assign same generation to spouses
    spouseRels.forEach(({ person1, person2 }) => {
      if (personGenerations.has(person1) && !personGenerations.has(person2)) {
        personGenerations.set(person2, personGenerations.get(person1)!);
        changed = true;
      } else if (personGenerations.has(person2) && !personGenerations.has(person1)) {
        personGenerations.set(person1, personGenerations.get(person2)!);
        changed = true;
      }
    });
  }
  
  // Step 3: Assign default generation to any remaining unprocessed people
  allPeople.forEach(person => {
    if (!personGenerations.has(person)) {
      personGenerations.set(person, 0); // Default to generation 0
    }
  });
  
  console.log('Generation assignments:', Object.fromEntries(personGenerations));
  
  // Step 4: Process parent-child relationships with assigned generations
  childParentRels.forEach((rel, index) => {
    setTimeout(() => {
      const { child, parent } = rel;
      const spouse = spouseMap.get(parent);
      
      const parentGen = personGenerations.get(parent)!;
      const childGen = personGenerations.get(child)!;
      
      console.log(`Processing: ${parent} (gen ${parentGen}) -> ${child} (gen ${childGen})`);
      
      // Add family relation with spouse if available
      addFamilyRelationWrapper(parent, "father", child, parentGen, childGen, spouse);
    }, index * 400);
  });

  return true; // Return true to indicate processing was successful
};