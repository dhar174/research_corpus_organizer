# Contributing to Research PDF Brain

Thank you for your interest in contributing to the Research PDF Brain project! This document provides guidelines and information for contributors.

## Ways to Contribute

### 1. Report Bugs
- Use GitHub Issues to report bugs
- Include steps to reproduce
- Provide error messages and logs
- Mention your environment (Colab, local, etc.)

### 2. Suggest Features
- Open an issue with the "enhancement" label
- Describe the use case
- Explain expected behavior
- Consider implementation complexity

### 3. Improve Documentation
- Fix typos and clarify instructions
- Add examples and use cases
- Improve code comments
- Update README, QUICKSTART, or ARCHITECTURE

### 4. Submit Code
- Fix bugs
- Implement new features
- Optimize performance
- Add tests

## Development Setup

### Prerequisites
- Python 3.8+
- Google Colab account (for testing)
- OpenAI API key (for testing)
- Git

### Local Development

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/research_corpus_organizer.git
   cd research_corpus_organizer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Testing in Colab

1. Upload your modified notebook to Google Colab
2. Set up configuration (API keys, folder paths)
3. Test with a small corpus (5-10 papers)
4. Verify all features work as expected

## Code Guidelines

### Python Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small

### Notebook Structure
- Keep cells focused on single tasks
- Add markdown explanations between code cells
- Include example outputs where helpful
- Clear cell outputs before committing

### Code Example
```python
def process_pdf(pdf_path: str) -> tuple[str, Dict]:
    """
    Extract text and metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (extracted_text, metadata_dict)
        
    Raises:
        PDFExtractionError: If PDF cannot be processed
    """
    # Implementation here
    pass
```

## Commit Guidelines

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb in imperative mood
- Keep first line under 50 characters
- Add detailed description if needed

Good examples:
- `Add citation extraction feature`
- `Fix PDF parsing for encrypted files`
- `Improve error handling in chunk agent`
- `Update documentation for RAG search`

Bad examples:
- `update`
- `fix bug`
- `changes`

### Commit Structure
```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how.

- Bullet points are okay
- Use present tense
- Reference issues: Fixes #123
```

## Pull Request Process

### Before Submitting

1. **Test thoroughly**
   - Test in Google Colab
   - Verify with sample PDFs
   - Check error handling
   - Ensure no regressions

2. **Update documentation**
   - Update README if needed
   - Add to CHANGELOG (if exists)
   - Update code comments
   - Add examples if appropriate

3. **Clean up code**
   - Remove debug prints
   - Clear notebook outputs
   - Remove commented code
   - Format code consistently

### Submitting

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use descriptive title
   - Reference related issues
   - Describe changes made
   - List testing performed
   - Add screenshots if UI changes

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Motivation and Context
   Why is this change needed? What problem does it solve?
   
   ## How Has This Been Tested?
   Describe testing performed
   
   ## Types of changes
   - [ ] Bug fix (non-breaking change which fixes an issue)
   - [ ] New feature (non-breaking change which adds functionality)
   - [ ] Breaking change (fix or feature that would cause existing functionality to change)
   - [ ] Documentation update
   
   ## Checklist
   - [ ] My code follows the code style of this project
   - [ ] I have updated the documentation accordingly
   - [ ] I have tested my changes in Google Colab
   - [ ] I have cleared notebook cell outputs
   ```

## Development Areas

### High Priority
- [ ] Citation extraction and parsing
- [ ] Figure and table extraction
- [ ] Incremental processing (skip already processed papers)
- [ ] Better error recovery
- [ ] Cost optimization

### Medium Priority
- [ ] Local embedding models (reduce API costs)
- [ ] Batch API processing
- [ ] Advanced search filters
- [ ] Export functionality (BibTeX, RIS)
- [ ] Paper recommendation system

### Low Priority
- [ ] Web interface
- [ ] Collaboration features
- [ ] Custom taxonomy training
- [ ] Integration with reference managers
- [ ] Advanced visualization

## Architecture Knowledge

Before contributing code, please read:
- `ARCHITECTURE.md` - System design and data flow
- `research_pdf_brain.ipynb` - Main implementation
- Existing code comments

Key concepts to understand:
- LangGraph state management
- Agent workflow pipeline
- FAISS vector search
- RAG implementation

## Code Review Process

### What We Look For

1. **Correctness**
   - Does it work as intended?
   - Are edge cases handled?
   - Is error handling appropriate?

2. **Code Quality**
   - Is it readable and maintainable?
   - Are functions well-named?
   - Is it properly documented?

3. **Performance**
   - Is it efficient?
   - Does it scale?
   - Are there unnecessary API calls?

4. **Compatibility**
   - Works in Google Colab?
   - No breaking changes?
   - Dependencies appropriate?

### Review Timeline
- Initial review: Within 1 week
- Follow-up: 2-3 days for revisions
- Merge: After approval from maintainer

## Testing Guidelines

### What to Test

1. **Core Functionality**
   - PDF ingestion (various formats)
   - Text extraction
   - Chunking
   - Summarization
   - Classification
   - Embedding generation
   - Search functionality

2. **Edge Cases**
   - Empty PDFs
   - Very large PDFs (100+ pages)
   - Corrupted files
   - Non-English text
   - Multiple languages
   - Scanned documents

3. **Error Handling**
   - API failures
   - Network issues
   - Invalid input
   - Out of memory

### Test Data
- Use publicly available papers (arXiv)
- Test with 5-10 papers minimum
- Include diverse topics and formats
- Don't commit large test files

## API Usage

### Responsible Usage
- Respect OpenAI rate limits
- Don't abuse the API
- Test with small batches first
- Monitor costs during development

### Cost Management
- Use development/test API keys
- Set usage limits in OpenAI dashboard
- Track costs during testing
- Optimize to reduce unnecessary calls

## Questions and Support

### Getting Help
- Check existing issues
- Read documentation thoroughly
- Ask in GitHub Discussions
- Provide context and examples

### Communication
- Be respectful and constructive
- Provide detailed information
- Be patient with responses
- Help others when possible

## Recognition

Contributors will be:
- Listed in README
- Mentioned in release notes
- Credited in commits
- Appreciated! 🎉

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Research PDF Brain! Your efforts help make this tool better for everyone in the research community.
