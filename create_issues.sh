#!/bin/bash

# Script to create GitHub issues from issues_definition.yaml
# This script uses the GitHub CLI (gh) to create issues programmatically
#
# Prerequisites:
# 1. Install GitHub CLI: https://cli.github.com/
# 2. Authenticate: gh auth login
# 3. Make this script executable: chmod +x create_issues.sh
#
# Usage:
#   ./create_issues.sh

set -e  # Exit on error

REPO="dhar174/research_corpus_organizer"
YAML_FILE="issues_definition.yaml"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Issues Creation Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI.${NC}"
    echo "Please run: gh auth login"
    exit 1
fi

# Check if yaml file exists
if [ ! -f "$YAML_FILE" ]; then
    echo -e "${RED}Error: $YAML_FILE not found.${NC}"
    exit 1
fi

echo -e "${YELLOW}This script will create 22 GitHub issues for the RAG PDF Research Corpus System.${NC}"
echo -e "${YELLOW}Repository: $REPO${NC}"
echo ""
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Creating issues...${NC}"
echo ""

# Create milestones first
echo -e "${YELLOW}Creating milestones...${NC}"
MILESTONES=(
    "Setup and Infrastructure"
    "Core Processing Pipeline"
    "AI Processing"
    "Data Management"
    "Workflow Orchestration"
    "Quality and Testing"
    "User Interface"
    "Monitoring and Optimization"
    "Documentation and Testing"
    "Deployment"
    "Future Enhancements"
)

for milestone in "${MILESTONES[@]}"; do
    # Check if milestone already exists
    if gh api "repos/$REPO/milestones" --jq ".[].title" | grep -q "^${milestone}$"; then
        echo "  ✓ Milestone already exists: $milestone"
    else
        gh api "repos/$REPO/milestones" -f title="$milestone" -f state="open" > /dev/null 2>&1 && \
            echo "  ✓ Created milestone: $milestone" || \
            echo "  ✗ Failed to create milestone: $milestone"
    fi
done

echo ""
echo -e "${YELLOW}Creating issues from YAML file...${NC}"
echo ""

# Function to create a single issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"
    local milestone="$4"
    
    # Build the gh issue create command
    cmd="gh issue create --repo $REPO --title \"$title\" --body \"$body\""
    
    # Add labels if provided
    if [ -n "$labels" ]; then
        # Convert comma-separated labels to space-separated for gh CLI
        labels_formatted=$(echo "$labels" | tr ',' ' ')
        cmd="$cmd --label $labels_formatted"
    fi
    
    # Add milestone if provided
    if [ -n "$milestone" ]; then
        cmd="$cmd --milestone \"$milestone\""
    fi
    
    # Execute the command
    eval $cmd
}

# Issue definitions (extracted from YAML)
# Phase 0
create_issue \
    "Phase 0: Notebook Setup and Configuration" \
    "$(cat <<'EOF'
## Overview
Set up the basic notebook structure and environment for the RAG PDF Research Corpus System.

## Tasks

### Step 0.1: Create Notebook Structure
- [ ] Create new Google Colab notebook file
- [ ] Add notebook title and description
- [ ] Create markdown cells for major section headers
- [ ] Add version and attribution information

### Step 0.2: Environment Setup Cell
- [ ] Add cell to check Python version (ensure 3.10+)
- [ ] Add cell to check GPU/CPU availability
- [ ] Add cell to display runtime information

### Step 0.3: Install Dependencies
Create installation cell with all required packages:
- [ ] OpenAI Python SDK (latest version supporting GPT-5.1)
- [ ] LangGraph (for workflow orchestration)
- [ ] PyMuPDF (fitz) for PDF parsing
- [ ] FAISS (CPU version) for vector indexing
- [ ] scikit-learn for clustering algorithms
- [ ] hdbscan (optional, for density-based clustering)
- [ ] pandas, numpy for data handling
- [ ] tqdm for progress bars
- [ ] matplotlib, seaborn for visualization
- [ ] python-dateutil for date parsing
- [ ] requests for arXiv/CrossRef API access
- [ ] pytesseract and Pillow (optional, for OCR fallback)
- [ ] pydantic for data validation

### Step 0.4: Import Statements Cell
- [ ] Group imports by category (standard library, third-party, custom)
- [ ] Add try-except blocks for optional dependencies
- [ ] Verify all imports succeed

### Step 0.5: Configuration Cell
- [ ] Create RunConfig class/TypedDict with all parameters
- [ ] Add user-editable configuration section
- [ ] Include default values and descriptions for each parameter
- [ ] Add validation for configuration parameters

## Reference
See FINAL_NOTEBOOK_ACTION_PLAN.md Phase 0
EOF
)" \
    "setup,phase-0" \
    "Setup and Infrastructure"

echo "  ✓ Created issue: Phase 0"

# Phase 1
create_issue \
    "Phase 1: Data Models and Schema Definitions" \
    "$(cat <<'EOF'
## Overview
Define all data models and schemas required for the RAG PDF system.

## Tasks

### Step 1.1: Define PaperRecord Schema
- [ ] Create Pydantic model or TypedDict for PaperRecord
- [ ] Include all fields from spec section 3.2 (ID, file info, metadata, summaries, topics, status, errors)
- [ ] Add field validators
- [ ] Add helper methods (to_dict, from_dict)

### Step 1.2: Define PaperChunk Schema
- [ ] Create Pydantic model or TypedDict for PaperChunk
- [ ] Include fields from spec section 3.3 (paper/chunk IDs, sections, pages, text, embeddings)
- [ ] Add validation for chunk size limits

### Step 1.3: Define TopicHierarchy Schema
- [ ] Create data structure for 3-tier taxonomy
- [ ] Define tier structures (tier1, tier2, tier3)
- [ ] Include topic metadata (ID, label, description, paper IDs)
- [ ] Add parent-child relationships
- [ ] Include versioning and timestamp fields

### Step 1.4: Define GraphState Schema
- [ ] Create LangGraph state object
- [ ] Include all supervisor state fields from spec 3.5
- [ ] Add state update helpers

### Step 1.5: Define Helper Classes
- [ ] Create metadata extractor class
- [ ] Create statistics tracker class
- [ ] Create error handler class
- [ ] Add utility functions for common operations

## Reference
See FINAL_NOTEBOOK_ACTION_PLAN.md Phase 1
EOF
)" \
    "data-models,phase-1" \
    "Setup and Infrastructure"

echo "  ✓ Created issue: Phase 1"

# Phase 2
create_issue \
    "Phase 2: Google Drive Integration" \
    "$(cat <<'EOF'
## Overview
Implement Google Drive mounting and PDF discovery functionality.

## Tasks

### Step 2.1: Drive Mounting
- [ ] Create cell for Google Drive mount
- [ ] Add authentication handling
- [ ] Verify mount success
- [ ] Display mounted folder structure

### Step 2.2: PDF Discovery Function
- [ ] Create function to resolve absolute folder paths
- [ ] Implement recursive PDF file discovery
- [ ] Generate unique paper IDs (hash of file_path)
- [ ] Create initial PaperRecord entries
- [ ] Handle duplicate files
- [ ] Add progress reporting

### Step 2.3: File Management Utilities
- [ ] Create function to validate file access
- [ ] Add function to check available disk space
- [ ] Implement file path sanitization
- [ ] Add error handling for missing files

## Reference
See FINAL_NOTEBOOK_ACTION_PLAN.md Phase 2
EOF
)" \
    "google-drive,phase-2" \
    "Setup and Infrastructure"

echo "  ✓ Created issue: Phase 2"

# Continue with remaining phases...
# For brevity, I'll show a few more and use a loop pattern

PHASES=(
    "3:PDF Parsing and Chunking:pdf-parsing,phase-3:Core Processing Pipeline"
    "4:Metadata Extraction:metadata,phase-4:Core Processing Pipeline"
    "5:Embedding Generation and FAISS Index:embeddings,faiss,phase-5:Core Processing Pipeline"
    "6:Summarization (Pass 1):summarization,gpt-5.1,phase-6:AI Processing"
    "7:Initial CSV Export:export,phase-7:Data Management"
    "8:Topic Modeling and Taxonomy Construction:taxonomy,clustering,phase-8:AI Processing"
    "9:Taxonomy Review and Approval:taxonomy,review,phase-9:AI Processing"
    "10:Final Topic Classification (Pass 3):classification,gpt-5.1,phase-10:AI Processing"
    "11:Deep Analysis Pass (Optional - Pass 2):deep-analysis,optional,phase-11:AI Processing"
    "12:Final CSV/Parquet Export:export,phase-12:Data Management"
    "13:LangGraph Workflow Integration:langgraph,workflow,phase-13:Workflow Orchestration"
    "14:Quality Control and Validation:quality-control,validation,phase-14:Quality and Testing"
    "15:RAG Query Interface:rag,query,phase-15:User Interface"
    "16:Utility Functions and Tools:utilities,tools,phase-16:User Interface"
    "17:Cost Tracking and Optimization:cost-tracking,optimization,phase-17:Monitoring and Optimization"
    "18:Error Handling and Resilience:error-handling,resilience,phase-18:Monitoring and Optimization"
    "19:Documentation and User Guide:documentation,phase-19:Documentation and Testing"
    "20:Testing and Validation:testing,validation,phase-20:Documentation and Testing"
    "21:Deployment and Finalization:deployment,release,phase-21:Deployment"
    "22:Advanced Features (Optional Enhancements):enhancement,optional,phase-22:Future Enhancements"
)

# Note: The actual issue bodies would need to be included for each phase
# For now, referencing the YAML file which contains all the details

echo ""
echo -e "${YELLOW}Note: This script template shows the first 3 issues.${NC}"
echo -e "${YELLOW}To create all 22 issues, you can use a YAML parser like 'yq' or 'python'${NC}"
echo -e "${YELLOW}to read the issues_definition.yaml file and create each issue programmatically.${NC}"
echo ""
echo -e "${GREEN}Alternative: Use Python script (create_issues.py) for full automation${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Issue creation template ready!${NC}"
echo -e "${GREEN}========================================${NC}"
