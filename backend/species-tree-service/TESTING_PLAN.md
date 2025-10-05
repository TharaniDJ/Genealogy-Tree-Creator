# Species Tree Service Testing Plan

## 3.1.3 Data Science Model Evaluation (Species-Specific)

### Technique Objective
To evaluate the accuracy of taxonomic relationship extraction and classification from Wikipedia Template:Taxonomy pages, ensuring reliable species hierarchy construction and taxonomic rank validation.

### Technique

#### Test 1: Taxonomic Relationship Extraction Accuracy

**Purpose**: Validate the accuracy of extracting parent-child taxonomic relationships from Wikipedia.

**Method**:
- Use manually curated ground truth dataset using Biopython library (NCBI datasets) with known taxonomic hierarchies
- Extract taxonomic relationships using `TaxonomyExtractor`model 'TaxonomyExpander'model (taxonomy Extractor: uses infoboxs taxonomy expander: uses llm and wikidata proprerties)
- Compare extracted relationships (parent_of, child_of) against ground truth
- Calculate precision, recall, and F1 score for each taxonomic rank level
- Perform error analysis on false positives and false negatives

**Test Data**:
100  diffrent species will be used
- Well-documented species: *Homo sapiens*, *Canis lupus*, *Tyrannosaurus rex*
- Complex taxonomic cases: *Tardigrada*, *Platypus* (Ornithorhynchus anatinus)
- Recently reclassified species: *Brontosaurus excelsus*

### Oracles

#### Test 1 Oracles:
- F1 scores calculated for each taxonomic rank level and overall extraction performance
- Precision and recall metrics per 

### Required Tools

**Python Libraries**:
- `requests` and `BeautifulSoup4` for Wikipedia scraping
- `pandas`, `numpy` for data analysis and ground truth management
- `scikit-learn` for metrics calculation (precision, recall, F1)
- `pytest` for automated testing framework
- `matplotlib`, `seaborn` for visualization of results

**Data Sources**:
- Wikipedia Template:Taxonomy pages
- NCBI Taxonomy database for validation

**Testing Infrastructure**:
- Automated test suite with parameterized test cases
- Performance benchmarking tools
- Error logging and analysis framework

### Success Criteria

#### Performance Benchmarks:
- **Test 1**: Overall F1 ≥0.80 across all taxonomic ranks
  - Kingdom level: F1 ≥0.80
  - Phylum level: F1 ≥0.80
  - Class level: F1 ≥0.80
  - Order level: F1 ≥0.80
  - Family level: F1 ≥0.80
  - Genus level: F1 ≥0.80
  - Species level: F1 ≥0.80

libs used: pandas numpy Biopython sikitlearn

*A. API Endpoint Testing*

1. **Taxonomy Extraction Endpoint (/api/v1/taxonomy/{scientific_name})**
   - *Valid Input Tests*:
     - Standard binomial nomenclature (e.g., "Homo sapiens", "Panthera leo")
     - Genus only inputs (e.g., "Homo", "Panthera")
     - Species with subspecies (e.g., "Panthera leo persica")
     - Common model organisms (e.g., "Drosophila melanogaster", "Mus musculus")
   
   - *Invalid Input Tests*:
     - Empty string input
     - Non-existent species names
     - Special characters and SQL injection attempts
     - Extremely long input strings (>1000 characters)
     - Numbers and invalid taxonomic formats
   
   - *Expected Responses*:
     - Valid inputs return TaxonomyTuplesResponse with correct hierarchical relationships
     - Invalid inputs return HTTP 404 with descriptive error messages
     - Malformed requests return HTTP 400 with validation errors

2. **Taxonomy Expansion Endpoint (/api/v1/expand/{taxon_name})**
   - *Valid Input Tests*:
     - Major taxonomic groups (e.g., "Mammalia", "Chordata", "Primates")
     - Different taxonomic ranks (kingdom, phylum, class, order, family, genus)
   
   - *Invalid Input Tests*:
     - Non-existent taxonomic names
     - Empty parameters
   
   - *Expected Responses*:
     - Valid inputs return ExpansionResponse with child taxa
     - Non-expandable taxa return empty children list
     - Invalid inputs return appropriate HTTP error codes

*B. Data Processing and Business Rules Testing*

1. *Wikipedia Integration*:
   - Extraction from Wikipedia Template:Taxonomy pages
   - Data sanitization and validation

2. *Taxonomic Hierarchy Rules*:
   - Correct parent-child relationships
   - Proper taxonomic rank ordering (domain → kingdom → phylum → class → order → family → genus → species)
   - Duplicate detection and prevention

### Oracles
The following strategies will be used to observe and validate test outcomes:

1. *Automated Response Validation*:
   - JSON schema validators for API responses
   - HTTP status code verification
   - Response time monitoring (< 5 seconds for standard requests)

3. *Error Handling Verification*:
   - Confirm appropriate error codes for different failure scenarios
   - Validate error message content and clarity
   - Test system recovery after failures

### Required Tools
The technique requires the following tools:

- *Test Automation Framework*: pytest for Python backend testing
- *API Testing Tools*: postmon

### Success Criteria
The technique supports the testing of:

- All key API endpoints with comprehensive input validation
- All major taxonomic hierarchies and expansion scenarios
- Error handling and recovery mechanisms
- Performance requirements (response times, concurrent users)
- Data accuracy and consistency requirements


## 3.1.3 User Interface Testing

#### UI Test Categories

*A. Search Interface Testing*

1. *Search Input Field*:
   - Text input functionality and validation
   - Placeholder text display
   - Input field focus and blur states
   - Keyboard navigation (tab, enter, escape)
   - Copy/paste functionality

2. *Search Button Interaction*:
   - Click functionality
   - Disabled state during loading
   - Visual feedback (hover, active states)
   - Keyboard accessibility (space, enter)


*B. Tree Visualization Testing*

1. *Node Display and Interaction*:
   - Node rendering with correct taxonomic information
   - Color coding by taxonomic rank
   - Node hover states and tooltips
   - Click-to-expand functionality
   - Wikipedia link integration

2. *Tree Layout and Navigation*:
   - Proper hierarchical arrangement
   - Zoom in/out functionality
   - Pan and drag navigation
   - Fit-to-view behavior
   - Minimap navigation (if available)

3. *Edge Connections*:
   - Proper parent-child connection lines
   - Visual hierarchy representation
   - Connection line styling and colors

*C. Interactive Features Testing*

1. *Node Expansion*:
   - Click to expand child nodes
   - Loading states during expansion
   - Prevention of duplicate expansions
   - Dynamic layout adjustment

2. *Wikipedia Integration*:
   - Wikipedia button functionality
   - External link opening behavior
   - Proper URL encoding for species names


*D. Responsive Design Testing*

1. *Screen Size Adaptability*:
   - Desktop display (1920x1080, 1366x768)
   - Tablet display (768x1024, 1024x768)

2. *Browser Compatibility*:
   - Chrome, Firefox, Safari, Edge
   - Different browser versions
   - JavaScript enabled/disabled scenarios

### Oracles
The following strategies will be used to accurately observe UI test outcomes:

1. *Visual Regression Testing*:
   - Screenshot comparison for consistent UI rendering
   - Cross-browser visual consistency validation

3. *Performance Monitoring*:
   - Page load time measurement
   - Tree rendering performance
   - Memory usage monitoring during large tree operations

4. *User Experience Validation*:
   - Task completion time measurement
   - Error recovery success rate
   - User interaction flow analysis



### Success Criteria
The technique supports the testing of:

- Each major screen or window that will be used extensively by the end user
- All interactive elements and their expected behaviors
- Responsive design across different device types
- Accessibility compliance for users with disabilities
- Performance standards for user experience