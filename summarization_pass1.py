#!/usr/bin/env python3
"""
Phase 6: Summarization (Pass 1) - Summary Generation Module

This module implements comprehensive summarization functionality for research papers
using GPT-5.1 with reasoning capabilities. It includes:

- Summary generator node for LangGraph workflows
- Prompt templates for high-quality academic summaries
- Initial analysis notes generation
- Batch processing with retries and rate limiting
- Summarization validation

Version: 1.0
Date: 2025-11-22
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available. Install with: pip install openai")

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logger.warning("tqdm not available. Progress bars will be disabled.")

from rag_models import (
    PaperRecord,
    PaperChunk,
    GraphState,
    RunConfig,
    StateManager,
)

# Export list for clean imports
__all__ = [
    # Step 6.1
    'SummaryGenerator',
    'summarize_paper_node',
    'create_summary_generator',
    
    # Step 6.2
    'SummaryPromptFactory',
    'create_summary_prompt',
    'create_notes_prompt',
    
    # Step 6.3
    'generate_initial_notes',
    'extract_key_insights',
    
    # Step 6.4
    'batch_summarize_papers',
    'summarize_papers_worker',
    
    # Step 6.5
    'validate_summary',
    'validate_paper_summaries',
    
    # Cost estimation
    'estimate_summarization_cost',
]


# =============================================================================
# Step 6.2: Summary Prompt Design
# =============================================================================

class SummaryPromptFactory:
    """
    Factory for creating structured prompts for paper summarization.
    
    Prompts are designed to extract comprehensive information from
    academic papers in a structured format.
    """
    
    @staticmethod
    def create_system_prompt(paper_type: str = "research paper") -> str:
        """
        Create system prompt for the summarization task.
        
        Args:
            paper_type: Type of paper (research paper, preprint, survey, etc.)
            
        Returns:
            System prompt string
        """
        return f"""You are an expert academic researcher tasked with creating comprehensive, 
structured summaries of {paper_type}s. Your summaries should be clear, accurate, and 
highlight the most important aspects of the research.

Your goal is to help researchers quickly understand:
- What the paper contributes to the field
- The problem being addressed
- The methodology used
- Key findings and results
- Significance and implications
- Any limitations or future work

Provide summaries that are:
- Accurate and faithful to the source material
- Structured with clear sections
- Comprehensive yet concise (2-4 paragraphs)
- Written in academic but accessible language
- Focused on the core contributions and insights"""
    
    @staticmethod
    def create_user_prompt(
        title: Optional[str],
        abstract: Optional[str],
        intro_text: Optional[str],
        methods_text: Optional[str],
        results_text: Optional[str],
        conclusion_text: Optional[str],
        max_length: int = 500
    ) -> str:
        """
        Create user prompt with paper content.
        
        Args:
            title: Paper title
            abstract: Abstract text
            intro_text: Introduction section text
            methods_text: Methods section text
            results_text: Results section text
            conclusion_text: Conclusion section text
            max_length: Maximum length per section in words
            
        Returns:
            User prompt string
        """
        sections = []
        
        if title:
            sections.append(f"**Title:** {title}\n")
        
        if abstract:
            sections.append(f"**Abstract:**\n{abstract}\n")
        
        if intro_text:
            truncated = SummaryPromptFactory._truncate_text(intro_text, max_length)
            sections.append(f"**Introduction (excerpt):**\n{truncated}\n")
        
        if methods_text:
            truncated = SummaryPromptFactory._truncate_text(methods_text, max_length)
            sections.append(f"**Methods (excerpt):**\n{truncated}\n")
        
        if results_text:
            truncated = SummaryPromptFactory._truncate_text(results_text, max_length)
            sections.append(f"**Results (excerpt):**\n{truncated}\n")
        
        if conclusion_text:
            truncated = SummaryPromptFactory._truncate_text(conclusion_text, max_length)
            sections.append(f"**Conclusion (excerpt):**\n{truncated}\n")
        
        content = "\n".join(sections)
        
        return f"""Please provide a comprehensive summary of this research paper with the following structure:

{content}

**Summary Requirements:**

1. **Main Contribution** (1-2 sentences): What is the primary contribution or novelty of this work?

2. **Problem Statement** (1-2 sentences): What problem does this paper address? What gap does it fill?

3. **Methodology** (2-3 sentences): What approach or methods did the authors use? What makes their approach unique or effective?

4. **Key Findings** (2-3 sentences): What are the main results or discoveries? Include any significant metrics or outcomes.

5. **Significance** (1-2 sentences): Why does this work matter? What are the implications for the field?

6. **Limitations** (1 sentence, optional): Any notable limitations or constraints mentioned by the authors?

Please provide a well-structured summary following this format."""
    
    @staticmethod
    def create_notes_prompt(
        title: Optional[str],
        abstract: Optional[str],
        summary: str
    ) -> str:
        """
        Create prompt for generating initial analysis notes.
        
        Args:
            title: Paper title
            abstract: Abstract text
            summary: Generated summary
            
        Returns:
            Notes generation prompt
        """
        return f"""Based on this research paper, provide concise initial analysis notes for a researcher:

**Title:** {title or "Unknown"}

**Abstract:** {abstract or "Not available"}

**Summary:**
{summary}

**Please provide:**

1. **Key Concepts**: List 3-5 important concepts, techniques, or terms introduced or used.

2. **Methodological Notes**: Brief notes on the research approach, experimental design, or analysis methods.

3. **Important Insights**: 2-3 key insights or takeaways that would be valuable for someone studying this area.

4. **Research Context**: How this work relates to or builds upon prior research (if mentioned).

Format the notes as brief, researcher-friendly bullet points."""
    
    @staticmethod
    def _truncate_text(text: str, max_words: int) -> str:
        """
        Truncate text to maximum word count.
        
        Args:
            text: Input text
            max_words: Maximum number of words
            
        Returns:
            Truncated text
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."


def create_summary_prompt(paper: PaperRecord, chunks: List[PaperChunk], config: RunConfig) -> Tuple[str, str]:
    """
    Create system and user prompts for summarizing a paper.
    
    Args:
        paper: PaperRecord to summarize
        chunks: List of paper chunks
        config: RunConfig with parameters
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Determine paper type
    paper_type = "preprint" if paper.is_preprint else "research paper"
    
    # Extract section texts from chunks
    section_texts = {
        "abstract": [],
        "introduction": [],
        "methods": [],
        "results": [],
        "conclusion": []
    }
    
    for chunk in chunks:
        section_label = chunk.section_label.lower()
        text = chunk.cleaned_text or chunk.text
        
        if section_label in section_texts:
            section_texts[section_label].append(text)
    
    # Join section texts
    abstract_text = paper.abstract_text or " ".join(section_texts["abstract"])
    intro_text = " ".join(section_texts["introduction"])
    methods_text = " ".join(section_texts["methods"])
    results_text = " ".join(section_texts["results"])
    conclusion_text = " ".join(section_texts["conclusion"])
    
    # Calculate max length per section to stay within token limits
    # Conservative estimate: 2000 tokens ~ 1500 words total
    max_section_words = 300
    
    system_prompt = SummaryPromptFactory.create_system_prompt(paper_type)
    user_prompt = SummaryPromptFactory.create_user_prompt(
        title=paper.title,
        abstract=abstract_text if abstract_text else None,
        intro_text=intro_text if intro_text else None,
        methods_text=methods_text if methods_text else None,
        results_text=results_text if results_text else None,
        conclusion_text=conclusion_text if conclusion_text else None,
        max_length=max_section_words
    )
    
    return system_prompt, user_prompt


def create_notes_prompt(paper: PaperRecord, summary: str) -> Tuple[str, str]:
    """
    Create prompts for generating initial analysis notes.
    
    Args:
        paper: PaperRecord
        summary: Generated summary text
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """You are an expert research analyst creating concise, actionable notes 
for academic researchers. Your notes should highlight key concepts, methodologies, and insights 
in a format that's easy to reference and understand."""
    
    user_prompt = SummaryPromptFactory.create_notes_prompt(
        title=paper.title,
        abstract=paper.abstract_text,
        summary=summary
    )
    
    return system_prompt, user_prompt


# =============================================================================
# Step 6.1: Summary Generator Node
# =============================================================================

@dataclass
class SummarizationStats:
    """Statistics for summarization operations."""
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    api_calls: int = 0
    estimated_cost_usd: float = 0.0
    papers_summarized: int = 0
    papers_failed: int = 0
    total_time_seconds: float = 0.0


class SummaryGenerator:
    """
    Generates comprehensive summaries for research papers using GPT-5.1.
    
    Handles API calls, retries, rate limiting, and cost tracking.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        reasoning_effort: str = "medium",
        max_tokens: int = 2000,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3
    ):
        """
        Initialize the summary generator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for summarization
            reasoning_effort: Reasoning effort level (none, low, medium, high)
            max_tokens: Maximum tokens for completion
            rate_limit_delay: Delay between API calls in seconds
            max_retries: Maximum number of retry attempts
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required. Install with: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_tokens = max_tokens
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        
        # Statistics tracking
        self.stats = SummarizationStats()
        
        logger.info(f"SummaryGenerator initialized with model={model}, reasoning_effort={reasoning_effort}")
    
    def generate_summary(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a summary using the OpenAI API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt with paper content
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Tuple of (summary_text, usage_stats)
        """
        # Build input for Responses API
        input_messages = [
            {"role": "user", "content": user_prompt}
        ]
        
        for attempt in range(self.max_retries):
            try:
                # Add rate limiting delay
                if self.stats.api_calls > 0:
                    time.sleep(self.rate_limit_delay)
                
                # Build request parameters for Responses API
                request_params = {
                    "model": self.model,
                    "instructions": system_prompt,  # Map system message to instructions
                    "input": input_messages,  # Convert messages to input array
                    "max_tokens": self.max_tokens,
                    "temperature": temperature,
                }
                
                # Add reasoning effort if supported
                if self.reasoning_effort != "none" and "gpt-5" in self.model.lower():
                    request_params["reasoning_effort"] = self.reasoning_effort
                
                start_time = time.time()
                response = self.client.responses.create(**request_params)
                elapsed = time.time() - start_time
                
                # Extract response from Responses API format
                # Response structure: response.output[0].content[0].text
                summary = ""
                if hasattr(response, 'output') and response.output and len(response.output) > 0:
                    output_item = response.output[0]
                    if hasattr(output_item, 'content') and len(output_item.content) > 0:
                        summary = output_item.content[0].text
                
                # Track usage
                usage_stats = {
                    "prompt_tokens": response.usage.input_tokens if hasattr(response.usage, 'input_tokens') else response.usage.prompt_tokens,
                    "completion_tokens": response.usage.output_tokens if hasattr(response.usage, 'output_tokens') else response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens if (response.usage is not None and hasattr(response.usage, 'total_tokens')) else 0,
                    "time_seconds": elapsed,
                    "model": self.model,
                }
                
                # Update cumulative stats
                self.stats.total_tokens += usage_stats["total_tokens"]
                self.stats.prompt_tokens += usage_stats["prompt_tokens"]
                self.stats.completion_tokens += usage_stats["completion_tokens"]
                self.stats.api_calls += 1
                self.stats.total_time_seconds += elapsed
                self.stats.estimated_cost_usd += self._estimate_call_cost(usage_stats["total_tokens"])
                
                return summary, usage_stats
                
            except Exception as e:
                logger.warning(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * self.rate_limit_delay
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts")
                    raise
        
        raise RuntimeError("Failed to generate summary")
    
    def _estimate_call_cost(self, tokens: int) -> float:
        """
        Estimate cost for a single API call.
        
        Args:
            tokens: Number of tokens used
            
        Returns:
            Estimated cost in USD
        """
        # Pricing as of Nov 2025 (approximate)
        cost_per_1m_tokens = {
            "gpt-5-mini": 0.15,  # Placeholder pricing
            "gpt-5.1": 0.30,       # Placeholder pricing (note: GPT-5.1 is a separate model from gpt-5-mini)
            "gpt-4-turbo": 10.00,
            "gpt-4": 30.00,
        }
        
        # Find matching model
        for model_key, price in cost_per_1m_tokens.items():
            if model_key in self.model.lower():
                return (tokens / 1_000_000) * price
        
        # Default estimate
        return (tokens / 1_000_000) * 0.15
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cumulative statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_tokens": self.stats.total_tokens,
            "prompt_tokens": self.stats.prompt_tokens,
            "completion_tokens": self.stats.completion_tokens,
            "api_calls": self.stats.api_calls,
            "estimated_cost_usd": self.stats.estimated_cost_usd,
            "papers_summarized": self.stats.papers_summarized,
            "papers_failed": self.stats.papers_failed,
            "total_time_seconds": self.stats.total_time_seconds,
            "avg_time_per_call": (
                self.stats.total_time_seconds / self.stats.api_calls 
                if self.stats.api_calls > 0 else 0
            ),
        }


def create_summary_generator(api_key: str, config: RunConfig) -> SummaryGenerator:
    """
    Create a SummaryGenerator from RunConfig.
    
    Args:
        api_key: OpenAI API key
        config: RunConfig with model settings
        
    Returns:
        SummaryGenerator instance
    """
    return SummaryGenerator(
        api_key=api_key,
        model=config.summary_model,
        reasoning_effort=config.summary_reasoning_effort,
        max_tokens=config.max_tokens_per_summary,
        rate_limit_delay=1.0,
        max_retries=3
    )


def summarize_paper_node(
    paper_id: str,
    state: GraphState,
    api_key: str
) -> GraphState:
    """
    LangGraph node to generate summary for a single paper.
    
    Args:
        paper_id: ID of paper to summarize
        state: Current GraphState
        api_key: OpenAI API key
        
    Returns:
        Updated GraphState
    """
    logger.info(f"Summarizing paper: {paper_id}")
    
    try:
        # Get paper and chunks
        paper = state["papers"][paper_id]
        chunks = state["chunks"].get(paper_id, [])
        
        if not chunks:
            logger.warning(f"No chunks found for paper {paper_id}, skipping summarization")
            state = StateManager.mark_paper_failed(
                state, paper_id, "No chunks available for summarization"
            )
            return state
        
        # Create generator
        config = state["config"]
        generator = create_summary_generator(api_key, config)
        
        # Create prompts
        system_prompt, user_prompt = create_summary_prompt(paper, chunks, config)
        
        # Generate summary
        summary, usage_stats = generator.generate_summary(system_prompt, user_prompt)
        
        # Update paper record
        state = StateManager.update_paper(state, paper_id, {
            "full_summary": summary,
            "processing_status": "summarized"
        })
        
        # Update stats
        if "stats" not in state:
            state["stats"] = {}
        
        state["stats"]["summarization_tokens"] = state["stats"].get("summarization_tokens", 0) + usage_stats["total_tokens"]
        state["stats"]["summarization_calls"] = state["stats"].get("summarization_calls", 0) + 1
        state["stats"]["summarization_cost_usd"] = state["stats"].get("summarization_cost_usd", 0.0) + generator._estimate_call_cost(usage_stats["total_tokens"])
        
        logger.info(f"Summary generated for {paper_id} ({usage_stats['total_tokens']} tokens)")
        
        return state
        
    except Exception as e:
        logger.error(f"Error summarizing paper {paper_id}: {e}")
        state = StateManager.mark_paper_failed(state, paper_id, f"Summarization error: {str(e)}")
        return state


# =============================================================================
# Step 6.3: Initial Notes Generation
# =============================================================================

def generate_initial_notes(
    paper_id: str,
    state: GraphState,
    api_key: str
) -> GraphState:
    """
    Generate initial analysis notes for a paper.
    
    Args:
        paper_id: ID of paper
        state: Current GraphState
        api_key: OpenAI API key
        
    Returns:
        Updated GraphState
    """
    logger.info(f"Generating initial notes for paper: {paper_id}")
    
    try:
        paper = state["papers"][paper_id]
        
        # Check if summary exists
        if not paper.full_summary:
            logger.warning(f"No summary available for {paper_id}, cannot generate notes")
            return state
        
        # Create generator
        config = state["config"]
        generator = create_summary_generator(api_key, config)
        
        # Create prompts for notes
        system_prompt, user_prompt = create_notes_prompt(paper, paper.full_summary)
        
        # Generate notes
        notes, usage_stats = generator.generate_summary(system_prompt, user_prompt, temperature=0.5)
        
        # Update paper record
        state = StateManager.update_paper(state, paper_id, {
            "initial_notes": notes
        })
        
        # Update stats
        if "stats" not in state:
            state["stats"] = {}
        
        state["stats"]["notes_tokens"] = state["stats"].get("notes_tokens", 0) + usage_stats["total_tokens"]
        state["stats"]["notes_calls"] = state["stats"].get("notes_calls", 0) + 1
        
        logger.info(f"Initial notes generated for {paper_id}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error generating notes for {paper_id}: {e}")
        # Don't fail the paper, notes are optional
        return state


def extract_key_insights(summary: str, notes: Optional[str] = None) -> List[str]:
    """
    Extract key insights from summary and notes.
    
    This is a simple extraction function that can be used for
    quick analysis without additional API calls.
    
    Args:
        summary: Summary text
        notes: Optional notes text
        
    Returns:
        List of key insight strings
    """
    insights = []
    
    # Extract sentences that indicate contributions or findings
    summary_sentences = summary.split('.')
    
    keywords = [
        "contribute", "novel", "innovative", "demonstrate", "show",
        "find", "discover", "propose", "introduce", "improve"
    ]
    
    for sentence in summary_sentences:
        sentence = sentence.strip()
        if any(keyword in sentence.lower() for keyword in keywords):
            insights.append(sentence + ".")
    
    return insights[:5]  # Return top 5 insights


# =============================================================================
# Step 6.4: Batch Processing with Retries
# =============================================================================

def batch_summarize_papers(
    state: GraphState,
    api_key: str,
    paper_ids: Optional[List[str]] = None,
    include_notes: bool = True,
    show_progress: bool = True
) -> GraphState:
    """
    Batch process papers for summarization.
    
    Args:
        state: Current GraphState
        api_key: OpenAI API key
        paper_ids: Optional list of specific paper IDs to process
        include_notes: Whether to generate initial notes
        show_progress: Whether to show progress bar
        
    Returns:
        Updated GraphState
    """
    # Determine which papers to process
    if paper_ids is None:
        # Process papers that haven't been summarized yet
        paper_ids = [
            pid for pid, paper in state["papers"].items()
            if paper.processing_status in ["pending", "parsed", "embedded"]
            and not paper.full_summary
        ]
    
    logger.info(f"Batch summarizing {len(paper_ids)} papers")
    
    # Create progress bar if available
    iterator = tqdm(paper_ids, desc="Summarizing papers") if (show_progress and TQDM_AVAILABLE) else paper_ids
    
    success_count = 0
    failure_count = 0
    
    for paper_id in iterator:
        try:
            # Generate summary
            state = summarize_paper_node(paper_id, state, api_key)
            
            # Check if summary was generated successfully
            paper = state["papers"][paper_id]
            if paper.full_summary:
                success_count += 1
                
                # Generate notes if requested
                if include_notes:
                    state = generate_initial_notes(paper_id, state, api_key)
            else:
                failure_count += 1
                
        except Exception as e:
            logger.error(f"Error processing paper {paper_id}: {e}")
            failure_count += 1
            state = StateManager.mark_paper_failed(state, paper_id, f"Batch processing error: {str(e)}")
    
    logger.info(f"Batch summarization complete: {success_count} succeeded, {failure_count} failed")
    
    # Update overall stats
    if "stats" not in state:
        state["stats"] = {}
    
    state["stats"]["papers_summarized"] = success_count
    state["stats"]["papers_failed_summary"] = failure_count
    
    return state


def summarize_papers_worker(state: GraphState, api_key: str) -> GraphState:
    """
    LangGraph worker node for Phase 6: Summarization Pass 1.
    
    This worker orchestrates the complete summarization workflow:
    1. Batch process all papers for summarization
    2. Generate initial notes for each paper
    3. Validate summaries
    4. Update state and statistics
    
    Args:
        state: Current GraphState
        api_key: OpenAI API key
        
    Returns:
        Updated GraphState with summaries and notes
    """
    logger.info("Starting Phase 6: Summarization Pass 1")
    
    start_time = time.time()
    
    # Update phase
    state["current_phase"] = "summarization_pass1"
    
    # Batch process all papers
    state = batch_summarize_papers(
        state=state,
        api_key=api_key,
        include_notes=True,
        show_progress=True
    )
    
    # Validate all summaries
    validation_results = validate_paper_summaries(state)
    
    # Update state with validation results
    state["stats"]["summary_validation"] = validation_results
    
    elapsed = time.time() - start_time
    state["stats"]["summarization_time_seconds"] = elapsed
    
    logger.info(f"Phase 6 complete in {elapsed:.1f} seconds")
    logger.info(f"Valid summaries: {validation_results['valid_count']}/{validation_results['total_count']}")
    
    return state


# =============================================================================
# Step 6.5: Summarization Validation
# =============================================================================

def validate_summary(summary: str, paper: PaperRecord) -> Dict[str, Any]:
    """
    Validate a single paper summary.
    
    Checks:
    - Summary is not empty
    - Summary has reasonable length
    - Summary contains key sections
    
    Args:
        summary: Summary text to validate
        paper: PaperRecord for context
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []
    
    # Check if summary exists
    if not summary or len(summary.strip()) == 0:
        issues.append("Summary is empty")
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "length": 0,
        }
    
    # Check length
    word_count = len(summary.split())
    if word_count < 50:
        issues.append(f"Summary too short ({word_count} words)")
    elif word_count < 100:
        warnings.append(f"Summary may be too brief ({word_count} words)")
    elif word_count > 1000:
        warnings.append(f"Summary may be too long ({word_count} words)")
    
    # Check for key sections/concepts
    summary_lower = summary.lower()
    
    expected_keywords = [
        ["contribution", "novel", "propose", "introduce"],
        ["method", "approach", "technique", "algorithm"],
        ["result", "finding", "demonstrate", "show"],
    ]
    
    missing_sections = []
    for i, keyword_group in enumerate(expected_keywords):
        if not any(kw in summary_lower for kw in keyword_group):
            section_names = ["contribution", "methodology", "results"]
            missing_sections.append(section_names[i])
    
    if missing_sections:
        warnings.append(f"Summary may be missing sections: {', '.join(missing_sections)}")
    
    # Check structure
    if "\n" not in summary and word_count > 200:
        warnings.append("Summary lacks paragraph structure")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "length": word_count,
        "has_structure": "\n" in summary,
        "missing_sections": missing_sections,
    }


def validate_paper_summaries(state: GraphState) -> Dict[str, Any]:
    """
    Validate all paper summaries in the state.
    
    Args:
        state: GraphState with papers
        
    Returns:
        Dictionary with validation statistics
    """
    valid_count = 0
    invalid_count = 0
    warning_count = 0
    
    all_issues = []
    all_warnings = []
    
    for paper_id, paper in state["papers"].items():
        if paper.full_summary:
            validation = validate_summary(paper.full_summary, paper)
            
            if validation["valid"]:
                valid_count += 1
            else:
                invalid_count += 1
                all_issues.extend(validation["issues"])
            
            if validation["warnings"]:
                warning_count += 1
                all_warnings.extend(validation["warnings"])
    
    total_count = len([p for p in state["papers"].values() if p.full_summary])
    
    return {
        "total_count": total_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "warning_count": warning_count,
        "issues": all_issues[:10],  # Top 10 issues
        "warnings": all_warnings[:10],  # Top 10 warnings
        "validation_rate": valid_count / total_count if total_count > 0 else 0,
    }


# =============================================================================
# Cost Estimation
# =============================================================================

def estimate_summarization_cost(
    num_papers: int,
    avg_paper_length_chars: int = 10000,
    model: str = "gpt-5-mini",
    include_notes: bool = True
) -> Dict[str, Any]:
    """
    Estimate cost for summarizing papers.
    
    Args:
        num_papers: Number of papers to summarize
        avg_paper_length_chars: Average paper length in characters
        model: Model to use
        include_notes: Whether to include notes generation
        
    Returns:
        Dictionary with cost estimate
    """
    # Estimate tokens per paper
    # Conservative: ~4 chars per token, plus prompt overhead
    tokens_per_paper = (avg_paper_length_chars // 4) + 500  # Prompt overhead
    completion_tokens = 500  # Average completion length
    
    total_tokens_summary = num_papers * (tokens_per_paper + completion_tokens)
    
    # Notes generation (if enabled)
    total_tokens_notes = 0
    if include_notes:
        # Notes are generated from summary, much smaller
        tokens_per_notes = 300 + 300  # Prompt + completion
        total_tokens_notes = num_papers * tokens_per_notes
    
    total_tokens = total_tokens_summary + total_tokens_notes
    
    # Pricing
    cost_per_1m_tokens = {
        "gpt-5-mini": 0.15,
        "gpt-5.1": 0.30,
        "gpt-4-turbo": 10.00,
        "gpt-4": 30.00,
    }
    
    price = 0.15  # Default
    for model_key, model_price in cost_per_1m_tokens.items():
        if model_key in model.lower():
            price = model_price
            break
    
    estimated_cost = (total_tokens / 1_000_000) * price
    
    return {
        "num_papers": num_papers,
        "avg_paper_length_chars": avg_paper_length_chars,
        "model": model,
        "include_notes": include_notes,
        "estimated_tokens": total_tokens,
        "estimated_tokens_summary": total_tokens_summary,
        "estimated_tokens_notes": total_tokens_notes,
        "estimated_cost_usd": estimated_cost,
        "cost_per_paper_usd": estimated_cost / num_papers if num_papers > 0 else 0,
    }
