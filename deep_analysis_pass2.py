#!/usr/bin/env python3
"""
Phase 11: Deep Analysis Pass (Optional - Pass 2) - Detailed Analysis Module

This module implements comprehensive deep analysis functionality for research papers
using GPT-5.1 with high reasoning effort. It includes:

- Deep analysis node for LangGraph workflows
- Prompt templates for detailed methodology and results analysis
- Detailed analysis focusing on methods, experimental setup, and results
- Batch processing with retries and rate limiting
- Deep analysis validation

Version: 1.0
Date: 2025-11-23
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
    # Step 11.1
    'should_perform_deep_analysis',
    'check_deep_analysis_flag',
    
    # Step 11.2
    'DeepAnalysisGenerator',
    'deep_analysis_node',
    'create_deep_analysis_generator',
    
    # Step 11.3
    'DeepAnalysisPromptFactory',
    'create_deep_analysis_prompt',
    
    # Step 11.4
    'batch_deep_analyze_papers',
    'deep_analyze_papers_worker',
    'select_papers_for_deep_analysis',
    
    # Validation
    'validate_deep_analysis',
    'validate_paper_deep_analyses',
    
    # Cost estimation
    'estimate_deep_analysis_cost',
]


# =============================================================================
# Step 11.1: Check Deep Analysis Flag
# =============================================================================

def should_perform_deep_analysis(config: RunConfig) -> bool:
    """
    Check if deep analysis pass should be performed.
    
    Args:
        config: RunConfig with enable_deep_analysis_pass flag
        
    Returns:
        True if deep analysis should be performed, False otherwise
    """
    return config.enable_deep_analysis_pass


def check_deep_analysis_flag(state: GraphState) -> bool:
    """
    Check deep analysis flag from GraphState.
    
    Args:
        state: GraphState with configuration
        
    Returns:
        True if deep analysis should be performed
    """
    if not state or not state.config:
        return False
    
    return should_perform_deep_analysis(state.config)


# =============================================================================
# Step 11.3: Deep Analysis Prompt Design
# =============================================================================

class DeepAnalysisPromptFactory:
    """
    Factory for creating structured prompts for deep paper analysis.
    
    Prompts are designed to extract detailed methodology, experimental
    setup, results, and limitations from academic papers.
    """
    
    @staticmethod
    def create_system_prompt() -> str:
        """
        Create system prompt for the deep analysis task.
        
        Returns:
            System prompt string
        """
        return """You are an expert academic researcher conducting in-depth analysis of research papers. 
Your task is to provide comprehensive, detailed analysis focusing on methodology, experimental 
setup, results, and implications.

Your analysis should be:
- Thorough and precise, capturing technical details
- Focused on reproducibility and understanding experimental design
- Critical but fair in evaluating methodology and results
- Comprehensive in extracting key metrics and findings
- Honest about limitations and future research directions

Provide analysis that would help a researcher:
- Understand exactly how experiments were conducted
- Reproduce the methodology if needed
- Evaluate the validity and significance of results
- Identify potential improvements or extensions
- Understand limitations and constraints"""
    
    @staticmethod
    def create_user_prompt(
        title: Optional[str],
        abstract: Optional[str],
        full_summary: Optional[str],
        methods_text: Optional[str],
        results_text: Optional[str],
        discussion_text: Optional[str],
        conclusion_text: Optional[str],
        max_length: int = 800
    ) -> str:
        """
        Create user prompt with paper content for deep analysis.
        
        Args:
            title: Paper title
            abstract: Abstract text
            full_summary: Previously generated summary (Pass 1)
            methods_text: Methods section text
            results_text: Results section text
            discussion_text: Discussion section text
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
        
        if full_summary:
            sections.append(f"**Previous Summary:**\n{full_summary}\n")
        
        if methods_text:
            truncated = DeepAnalysisPromptFactory._truncate_text(methods_text, max_length)
            sections.append(f"**Methods:**\n{truncated}\n")
        
        if results_text:
            truncated = DeepAnalysisPromptFactory._truncate_text(results_text, max_length)
            sections.append(f"**Results:**\n{truncated}\n")
        
        if discussion_text:
            truncated = DeepAnalysisPromptFactory._truncate_text(discussion_text, max_length)
            sections.append(f"**Discussion:**\n{truncated}\n")
        
        if conclusion_text:
            truncated = DeepAnalysisPromptFactory._truncate_text(conclusion_text, max_length)
            sections.append(f"**Conclusion:**\n{truncated}\n")
        
        content = "\n".join(sections)
        
        return f"""Please provide a detailed, in-depth analysis of this research paper with the following structure:

{content}

**Deep Analysis Requirements:**

1. **Detailed Methodology Breakdown** (3-4 sentences):
   - What specific algorithms, techniques, or approaches were used?
   - What datasets, tools, or frameworks were employed?
   - What were the key design choices and why were they made?

2. **Experimental Setup Details** (3-4 sentences):
   - How were experiments designed and structured?
   - What parameters, configurations, or settings were used?
   - What baselines or comparisons were established?
   - How was evaluation performed?

3. **Key Results and Metrics** (3-4 sentences):
   - What were the quantitative results (include specific metrics and values)?
   - What were the qualitative findings?
   - How do results compare to baselines or state-of-the-art?
   - What statistical significance or confidence measures were reported?

4. **Limitations and Constraints** (2-3 sentences):
   - What limitations did the authors acknowledge?
   - What constraints affected the study (data, computational, methodological)?
   - What assumptions were made?

5. **Future Work and Extensions** (2-3 sentences):
   - What future research directions did the authors suggest?
   - What potential improvements or extensions are possible?
   - What open questions remain?

6. **Comprehensive Notes** (3-4 bullet points):
   - Technical details important for reproduction
   - Key insights about the approach or methodology
   - Notable findings or surprises
   - Relevance to current research trends

Please provide a thorough, detailed analysis following this format."""
    
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


def create_deep_analysis_prompt(
    paper: PaperRecord, 
    chunks: List[PaperChunk], 
    config: RunConfig
) -> Tuple[str, str]:
    """
    Create system and user prompts for deep analysis of a paper.
    
    Args:
        paper: PaperRecord to analyze
        chunks: List of paper chunks
        config: RunConfig with parameters
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Extract section texts from chunks
    section_texts = {
        "abstract": [],
        "methods": [],
        "methodology": [],
        "approach": [],
        "results": [],
        "experiments": [],
        "evaluation": [],
        "discussion": [],
        "conclusion": []
    }
    
    for chunk in chunks:
        section_label = chunk.section_label.lower()
        text = chunk.cleaned_text or chunk.text
        
        # Match section labels flexibly
        for key in section_texts.keys():
            if key in section_label or section_label in key:
                section_texts[key].append(text)
                break
    
    # Join section texts
    abstract_text = paper.abstract_text or " ".join(section_texts["abstract"])
    
    # Combine methods-related sections
    methods_text = " ".join(
        section_texts["methods"] + 
        section_texts["methodology"] + 
        section_texts["approach"]
    )
    
    # Combine results-related sections
    results_text = " ".join(
        section_texts["results"] + 
        section_texts["experiments"] + 
        section_texts["evaluation"]
    )
    
    discussion_text = " ".join(section_texts["discussion"])
    conclusion_text = " ".join(section_texts["conclusion"])
    
    # Use larger max_section_words for deep analysis
    max_section_words = 800
    
    system_prompt = DeepAnalysisPromptFactory.create_system_prompt()
    user_prompt = DeepAnalysisPromptFactory.create_user_prompt(
        title=paper.title,
        abstract=abstract_text if abstract_text else None,
        full_summary=paper.full_summary,
        methods_text=methods_text if methods_text else None,
        results_text=results_text if results_text else None,
        discussion_text=discussion_text if discussion_text else None,
        conclusion_text=conclusion_text if conclusion_text else None,
        max_length=max_section_words
    )
    
    return system_prompt, user_prompt


# =============================================================================
# Step 11.2: Deep Analysis Generator Node
# =============================================================================

@dataclass
class DeepAnalysisStats:
    """Statistics for deep analysis operations."""
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    api_calls: int = 0
    estimated_cost_usd: float = 0.0
    papers_analyzed: int = 0
    papers_failed: int = 0
    total_time_seconds: float = 0.0


class DeepAnalysisGenerator:
    """
    Generates comprehensive deep analysis for research papers using GPT-5.1.
    
    Handles API calls, retries, rate limiting, and cost tracking.
    Focuses on detailed methodology and results analysis.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5.1",
        reasoning_effort: str = "high",
        max_tokens: int = 4000,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3
    ):
        """
        Initialize the deep analysis generator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for deep analysis (default: gpt-5.1)
            reasoning_effort: Reasoning effort level (default: high)
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
        self.stats = DeepAnalysisStats()
        
        logger.info(f"DeepAnalysisGenerator initialized with model={model}, reasoning_effort={reasoning_effort}")
    
    def generate_deep_analysis(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a deep analysis using the OpenAI API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt with paper content
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Tuple of (deep_analysis_text, usage_stats)
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
                    "instructions": system_prompt,
                    "input": input_messages,
                    "max_tokens": self.max_tokens,
                    "temperature": temperature,
                }
                
                # Add reasoning effort for GPT-5.1
                if self.reasoning_effort != "none" and "gpt-5" in self.model.lower():
                    request_params["reasoning_effort"] = self.reasoning_effort
                
                start_time = time.time()
                response = self.client.responses.create(**request_params)
                elapsed = time.time() - start_time
                
                # Extract response
                deep_analysis = response.choices[0].message.content
                
                # Track usage
                usage_stats = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
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
                
                return deep_analysis, usage_stats
                
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
        
        raise RuntimeError("Failed to generate deep analysis")
    
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
            "gpt-5-mini": 0.15,
            "gpt-5.1": 0.30,
            "gpt-4-turbo": 10.00,
            "gpt-4": 30.00,
        }
        
        # Find matching model
        for model_key, price in cost_per_1m_tokens.items():
            if model_key in self.model.lower():
                return (tokens / 1_000_000) * price
        
        # Default estimate
        return (tokens / 1_000_000) * 0.30
    
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
            "papers_analyzed": self.stats.papers_analyzed,
            "papers_failed": self.stats.papers_failed,
            "total_time_seconds": self.stats.total_time_seconds,
        }
    
    def analyze_paper(
        self,
        paper: PaperRecord,
        chunks: List[PaperChunk],
        config: RunConfig
    ) -> PaperRecord:
        """
        Perform deep analysis on a single paper.
        
        Args:
            paper: PaperRecord to analyze
            chunks: List of paper chunks
            config: RunConfig with parameters
            
        Returns:
            Updated PaperRecord with deep_summary
        """
        try:
            # Create prompts
            system_prompt, user_prompt = create_deep_analysis_prompt(paper, chunks, config)
            
            # Generate deep analysis
            deep_analysis, usage_stats = self.generate_deep_analysis(
                system_prompt,
                user_prompt
            )
            
            # Update paper record
            paper.deep_summary = deep_analysis
            paper.processing_status = "deep_analyzed"
            paper.last_updated = datetime.now()
            
            self.stats.papers_analyzed += 1
            
            logger.info(f"Deep analysis generated for paper {paper.id} ({paper.title})")
            logger.debug(f"Usage: {usage_stats['total_tokens']} tokens, {usage_stats['time_seconds']:.2f}s")
            
            return paper
            
        except Exception as e:
            logger.error(f"Failed to analyze paper {paper.id}: {e}")
            paper.error_reason = str(e)
            paper.error_stage = "deep_analysis"
            paper.retry_count += 1
            self.stats.papers_failed += 1
            raise


def create_deep_analysis_generator(config: RunConfig, api_key: str) -> DeepAnalysisGenerator:
    """
    Create a DeepAnalysisGenerator from RunConfig.
    
    Args:
        config: RunConfig with model and reasoning settings
        api_key: OpenAI API key
        
    Returns:
        Configured DeepAnalysisGenerator instance
    """
    # Use gpt-5.1 for deep analysis with high reasoning effort
    model = "gpt-5.1" if config.enable_deep_analysis_pass else config.summary_model
    reasoning_effort = "high"  # Always use high reasoning for deep analysis
    
    return DeepAnalysisGenerator(
        api_key=api_key,
        model=model,
        reasoning_effort=reasoning_effort,
        max_tokens=4000,  # Larger token limit for detailed analysis
        rate_limit_delay=1.0,
        max_retries=3
    )


def deep_analysis_node(
    paper_id: str,
    state: GraphState,
    generator: Optional[DeepAnalysisGenerator] = None
) -> GraphState:
    """
    LangGraph node for deep analysis of a paper.
    
    Args:
        paper_id: ID of paper to analyze
        state: Current GraphState
        generator: Optional pre-configured DeepAnalysisGenerator
        
    Returns:
        Updated GraphState
    """
    # Check if deep analysis should be performed
    if not check_deep_analysis_flag(state):
        logger.info("Deep analysis pass is disabled, skipping")
        return state
    
    # Get paper from state
    paper = state.papers.get(paper_id)
    if not paper:
        logger.error(f"Paper {paper_id} not found in state")
        return state
    
    # Get chunks for this paper
    chunks = [c for c in state.chunks if c.paper_id == paper_id]
    
    # Create generator if not provided
    if generator is None:
        if not state.config:
            logger.error("No config available in state")
            return state
        
        # Would need API key from environment or state
        # This is a placeholder - actual implementation would get key from state
        api_key = getattr(state, 'openai_api_key', None)
        if not api_key:
            logger.error("No OpenAI API key available")
            return state
        
        generator = create_deep_analysis_generator(state.config, api_key)
    
    # Perform deep analysis
    try:
        updated_paper = generator.analyze_paper(paper, chunks, state.config)
        state.papers[paper_id] = updated_paper
        logger.info(f"Deep analysis completed for {paper_id}")
    except Exception as e:
        logger.error(f"Deep analysis failed for {paper_id}: {e}")
    
    return state


# =============================================================================
# Step 11.4: Process Selected Papers
# =============================================================================

def select_papers_for_deep_analysis(
    papers: Dict[str, PaperRecord],
    config: RunConfig,
    subset_criteria: Optional[str] = None
) -> List[str]:
    """
    Select papers for deep analysis based on criteria.
    
    Args:
        papers: Dictionary of paper IDs to PaperRecords
        config: RunConfig
        subset_criteria: Optional criteria for selecting subset
                         ('all', 'classified', 'high_confidence', or list of IDs)
        
    Returns:
        List of paper IDs to analyze
    """
    if not should_perform_deep_analysis(config):
        return []
    
    # Default to all papers that have been summarized
    eligible_papers = [
        pid for pid, paper in papers.items()
        if paper.processing_status in ["summarized", "embedded", "classified"]
        and paper.full_summary is not None
    ]
    
    # Apply subset criteria if provided
    if subset_criteria is None or subset_criteria == "all":
        return eligible_papers
    
    elif subset_criteria == "classified":
        # Only papers that have been classified
        return [
            pid for pid in eligible_papers
            if papers[pid].tier1_topic is not None
        ]
    
    elif subset_criteria == "high_confidence":
        # Only papers with high classification confidence
        return [
            pid for pid in eligible_papers
            if papers[pid].tier1_confidence is not None
            and papers[pid].tier1_confidence >= 0.8
        ]
    
    elif isinstance(subset_criteria, list):
        # Specific list of paper IDs
        return [pid for pid in subset_criteria if pid in eligible_papers]
    
    else:
        logger.warning(f"Unknown subset criteria: {subset_criteria}, using all eligible papers")
        return eligible_papers


def batch_deep_analyze_papers(
    papers: Dict[str, PaperRecord],
    chunks: List[PaperChunk],
    config: RunConfig,
    api_key: str,
    subset_criteria: Optional[str] = None,
    max_papers: Optional[int] = None
) -> Tuple[Dict[str, PaperRecord], Dict[str, Any]]:
    """
    Perform deep analysis on a batch of papers.
    
    Args:
        papers: Dictionary of paper IDs to PaperRecords
        chunks: List of all paper chunks
        config: RunConfig with settings
        api_key: OpenAI API key
        subset_criteria: Optional criteria for selecting papers
        max_papers: Optional limit on number of papers to process
        
    Returns:
        Tuple of (updated_papers_dict, batch_stats)
    """
    # Check if deep analysis should be performed
    if not should_perform_deep_analysis(config):
        logger.info("Deep analysis pass is disabled")
        return papers, {"papers_analyzed": 0, "skipped": True}
    
    # Select papers to analyze
    paper_ids = select_papers_for_deep_analysis(papers, config, subset_criteria)
    
    # Apply max_papers limit if specified
    if max_papers is not None and len(paper_ids) > max_papers:
        paper_ids = paper_ids[:max_papers]
        logger.info(f"Limited to first {max_papers} papers")
    
    if not paper_ids:
        logger.info("No papers selected for deep analysis")
        return papers, {"papers_analyzed": 0, "no_eligible_papers": True}
    
    logger.info(f"Starting deep analysis for {len(paper_ids)} papers")
    
    # Create generator
    generator = create_deep_analysis_generator(config, api_key)
    
    # Process each paper
    updated_papers = papers.copy()
    
    iterator = tqdm(paper_ids, desc="Deep Analysis") if TQDM_AVAILABLE else paper_ids
    
    for paper_id in iterator:
        paper = updated_papers[paper_id]
        paper_chunks = [c for c in chunks if c.paper_id == paper_id]
        
        try:
            updated_paper = generator.analyze_paper(paper, paper_chunks, config)
            updated_papers[paper_id] = updated_paper
            
            if TQDM_AVAILABLE and hasattr(iterator, 'set_postfix'):
                iterator.set_postfix({
                    'analyzed': generator.stats.papers_analyzed,
                    'failed': generator.stats.papers_failed
                })
        
        except Exception as e:
            logger.error(f"Failed to deep analyze paper {paper_id}: {e}")
            continue
    
    # Get final statistics
    stats = generator.get_stats()
    stats['total_papers_selected'] = len(paper_ids)
    
    logger.info(f"Deep analysis complete: {stats['papers_analyzed']} analyzed, {stats['papers_failed']} failed")
    logger.info(f"Total cost: ${stats['estimated_cost_usd']:.2f}")
    
    return updated_papers, stats


def deep_analyze_papers_worker(
    state: GraphState,
    api_key: str,
    subset_criteria: Optional[str] = None,
    max_papers: Optional[int] = None
) -> GraphState:
    """
    Worker function for deep analyzing papers in LangGraph workflow.
    
    Args:
        state: Current GraphState
        api_key: OpenAI API key
        subset_criteria: Optional criteria for selecting papers
        max_papers: Optional limit on number of papers
        
    Returns:
        Updated GraphState
    """
    updated_papers, stats = batch_deep_analyze_papers(
        papers=state.papers,
        chunks=state.chunks,
        config=state.config,
        api_key=api_key,
        subset_criteria=subset_criteria,
        max_papers=max_papers
    )
    
    state.papers = updated_papers
    
    # Store stats in state metadata if available
    if hasattr(state, 'metadata') and state.metadata is not None:
        state.metadata['deep_analysis_stats'] = stats
    
    return state


# =============================================================================
# Validation Functions
# =============================================================================

def validate_deep_analysis(deep_analysis: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a deep analysis output.
    
    Args:
        deep_analysis: Deep analysis text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not deep_analysis:
        return False, "Deep analysis is empty or None"
    
    if len(deep_analysis.strip()) < 100:
        return False, "Deep analysis is too short (< 100 characters)"
    
    # Check for expected sections (flexible matching)
    expected_keywords = [
        "methodology", "method", "approach",
        "experiment", "result", "finding",
        "limitation", "future"
    ]
    
    deep_analysis_lower = deep_analysis.lower()
    found_keywords = sum(1 for kw in expected_keywords if kw in deep_analysis_lower)
    
    if found_keywords < 3:
        return False, f"Deep analysis missing expected content (found {found_keywords}/{len(expected_keywords)} keywords)"
    
    return True, None


def validate_paper_deep_analyses(
    papers: Dict[str, PaperRecord]
) -> Dict[str, Any]:
    """
    Validate deep analyses for all papers.
    
    Args:
        papers: Dictionary of paper IDs to PaperRecords
        
    Returns:
        Dictionary with validation results
    """
    total_papers = len(papers)
    deep_analyzed_papers = [p for p in papers.values() if p.deep_summary is not None]
    
    valid_analyses = []
    invalid_analyses = []
    
    for paper in deep_analyzed_papers:
        is_valid, error = validate_deep_analysis(paper.deep_summary)
        if is_valid:
            valid_analyses.append(paper.id)
        else:
            invalid_analyses.append({
                "paper_id": paper.id,
                "title": paper.title,
                "error": error
            })
    
    results = {
        "total_papers": total_papers,
        "papers_with_deep_analysis": len(deep_analyzed_papers),
        "valid_deep_analyses": len(valid_analyses),
        "invalid_deep_analyses": len(invalid_analyses),
        "validation_rate": len(valid_analyses) / len(deep_analyzed_papers) if deep_analyzed_papers else 0,
        "invalid_details": invalid_analyses
    }
    
    return results


# =============================================================================
# Cost Estimation
# =============================================================================

def estimate_deep_analysis_cost(
    num_papers: int,
    avg_paper_length_chars: int = 8000,
    model: str = "gpt-5.1",
) -> Dict[str, Any]:
    """
    Estimate cost for deep analysis of papers.
    
    Args:
        num_papers: Number of papers to analyze
        avg_paper_length_chars: Average paper length in characters
        model: Model to use for analysis
        
    Returns:
        Dictionary with cost estimates
    """
    # Estimate tokens per paper (rough approximation: 1 token ~= 4 chars)
    # Deep analysis uses more content (methods, results, discussion)
    chars_per_paper = avg_paper_length_chars * 1.5  # More content than basic summary
    tokens_per_paper_input = chars_per_paper / 4
    
    # Assume generous output for deep analysis
    tokens_per_paper_output = 1500  # Detailed analysis
    
    total_input_tokens = int(num_papers * tokens_per_paper_input)
    total_output_tokens = int(num_papers * tokens_per_paper_output)
    total_tokens = total_input_tokens + total_output_tokens
    
    # Pricing (approximate)
    cost_per_1m_tokens = {
        "gpt-5-mini": 0.15,
        "gpt-5.1": 0.30,
        "gpt-4-turbo": 10.00,
    }
    
    # Find matching model pricing
    price = 0.30  # Default
    for model_key, model_price in cost_per_1m_tokens.items():
        if model_key in model.lower():
            price = model_price
            break
    
    estimated_cost = (total_tokens / 1_000_000) * price
    cost_per_paper = estimated_cost / num_papers if num_papers > 0 else 0
    
    return {
        "num_papers": num_papers,
        "avg_paper_length_chars": avg_paper_length_chars,
        "estimated_input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
        "estimated_total_tokens": total_tokens,
        "model": model,
        "price_per_1m_tokens": price,
        "estimated_cost_usd": estimated_cost,
        "cost_per_paper_usd": cost_per_paper,
    }
