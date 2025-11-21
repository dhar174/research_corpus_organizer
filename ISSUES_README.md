# Creating GitHub Issues from Action Plan

This directory contains tools to automatically create GitHub issues from the `FINAL_NOTEBOOK_ACTION_PLAN.md` file.

## Overview

The action plan has been parsed into 22 comprehensive issues, one for each phase of the RAG PDF Research Corpus System implementation. Each issue includes:

- Detailed task lists with checkboxes
- Appropriate labels for categorization
- Milestone assignments for project tracking
- References back to the original action plan

## Files

- **`issues_definition.yaml`** - YAML file containing all 22 issue definitions with full content
- **`create_issues.py`** - Python script to create issues using GitHub CLI (recommended)
- **`create_issues.sh`** - Bash script template for issue creation
- **`ISSUES_README.md`** - This file

## Prerequisites

### Option 1: Using Python Script (Recommended)

1. **Install GitHub CLI**
   ```bash
   # macOS
   brew install gh
   
   # Windows
   winget install --id GitHub.cli
   
   # Linux
   # See https://github.com/cli/cli/blob/trunk/docs/install_linux.md
   ```

2. **Authenticate with GitHub**
   ```bash
   gh auth login
   ```

3. **Install PyYAML**
   ```bash
   pip install pyyaml
   ```

### Option 2: Using Bash Script

1. Install GitHub CLI (same as above)
2. Authenticate with GitHub (same as above)

## Usage

### Python Script (Recommended)

The Python script provides the most complete automation:

```bash
# Dry run - see what would be created without actually creating issues
python create_issues.py --dry-run

# Create all issues
python create_issues.py

# Create issues in a different repository
python create_issues.py --repo owner/repo-name

# Use a different YAML file
python create_issues.py --yaml-file custom_issues.yaml
```

### Bash Script (Template)

The bash script provides a starting template:

```bash
./create_issues.sh
```

Note: The bash script includes only the first few issues as examples. For complete automation, use the Python script.

### Manual Creation via GitHub CLI

You can also create issues manually using the GitHub CLI:

```bash
gh issue create --title "Issue Title" --body "Issue body" --label label1,label2 --milestone "Milestone Name"
```

## Issue Structure

The 22 issues are organized into these milestones:

1. **Setup and Infrastructure** (Phases 0-2)
   - Phase 0: Notebook Setup and Configuration
   - Phase 1: Data Models and Schema Definitions
   - Phase 2: Google Drive Integration

2. **Core Processing Pipeline** (Phases 3-5)
   - Phase 3: PDF Parsing and Chunking
   - Phase 4: Metadata Extraction
   - Phase 5: Embedding Generation and FAISS Index

3. **AI Processing** (Phases 6, 8-11)
   - Phase 6: Summarization (Pass 1)
   - Phase 8: Topic Modeling and Taxonomy Construction
   - Phase 9: Taxonomy Review and Approval
   - Phase 10: Final Topic Classification (Pass 3)
   - Phase 11: Deep Analysis Pass (Optional)

4. **Data Management** (Phases 7, 12)
   - Phase 7: Initial CSV Export
   - Phase 12: Final CSV/Parquet Export

5. **Workflow Orchestration** (Phase 13)
   - Phase 13: LangGraph Workflow Integration

6. **Quality and Testing** (Phase 14)
   - Phase 14: Quality Control and Validation

7. **User Interface** (Phases 15-16)
   - Phase 15: RAG Query Interface
   - Phase 16: Utility Functions and Tools

8. **Monitoring and Optimization** (Phases 17-18)
   - Phase 17: Cost Tracking and Optimization
   - Phase 18: Error Handling and Resilience

9. **Documentation and Testing** (Phases 19-20)
   - Phase 19: Documentation and User Guide
   - Phase 20: Testing and Validation

10. **Deployment** (Phase 21)
    - Phase 21: Deployment and Finalization

11. **Future Enhancements** (Phase 22)
    - Phase 22: Advanced Features (Optional Enhancements)

## Labels

Issues are tagged with the following labels:

- **Phase labels**: `phase-0` through `phase-22`

Each issue is labeled with its corresponding phase number for easy filtering and organization.

## Customization

To customize the issues before creation:

1. Edit `issues_definition.yaml`
2. Modify issue titles, bodies, labels, or milestones
3. Run the creation script

## Verification

After running the script, you can verify the issues were created:

```bash
# List all open issues
gh issue list --repo dhar174/research_corpus_organizer

# List issues by milestone
gh issue list --milestone "Setup and Infrastructure"

# List issues by label
gh issue list --label phase-0
```

## Troubleshooting

### Authentication Issues
```bash
# Check auth status
gh auth status

# Re-authenticate if needed
gh auth login
```

### Permission Issues
Make sure you have write access to the repository.

### Rate Limiting
If you encounter rate limiting, the script will pause between requests. GitHub CLI handles authentication tokens automatically.

### YAML Parsing Errors
Ensure `pyyaml` is installed:
```bash
pip install pyyaml
```

## Next Steps

After creating the issues:

1. Review the issues in the GitHub repository
2. Assign issues to team members
3. Set up a project board for tracking progress
4. Begin implementation following the issue order
5. Check off tasks as they are completed
6. Close issues when phases are fully implemented

## Additional Resources

- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub Issues Documentation](https://docs.github.com/en/issues)
- [Original Action Plan](./FINAL_NOTEBOOK_ACTION_PLAN.md)
- [Technical Specification](./rag_pdf_system_spec_v_2.md)
