"""Email response matching service using keyword matching."""

import logging
from typing import Optional, Tuple
from difflib import SequenceMatcher
from .models import Email

logger = logging.getLogger(__name__)


class ResponseMatcher:
    """Matches email questions to responses from a document using keyword matching."""

    def __init__(self, similarity_threshold: float = 0.4):
        """Initialize response matcher.
        
        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider a match.
        """
        self.similarity_threshold = similarity_threshold

    def find_response(
        self, email: Email, document_content: str
    ) -> Tuple[Optional[str], float]:
        """
        Find a matching response for an email from document content.
        Returns (response_text, confidence_score).
        """
        # Extract the main question from the email
        question_text = self._extract_question_text(email)
        
        # Parse Q&A pairs from document
        qa_pairs = self._parse_qa_pairs(document_content)
        
        if not qa_pairs:
            logger.warning("No Q&A pairs found in document")
            return None, 0.0
        
        matches = []
        
        for faq_question, faq_answer in qa_pairs:
            faq_question_lower = faq_question.lower().strip()
            similarity_score = self._calculate_similarity(question_text, faq_question_lower)
            
            if similarity_score >= self.similarity_threshold:
                matches.append((faq_answer.strip(), similarity_score))
        
        # Return best match
        if matches:
            best_match = max(matches, key=lambda x: x[1])
            logger.info(
                f"Found Q&A match with confidence {best_match[1]:.2%}"
            )
            return best_match
        else:
            logger.info("No matching Q&A found")
            return None, 0.0

    def _extract_question_text(self, email: Email) -> str:
        """Extract the main question text from an email, filtering out signatures and noise."""
        subject_lower = email.subject.lower().strip()
        body = email.body.strip()
        
        # If subject is generic or very short, focus on body
        generic_subjects = ['inquiry', 'question', 'help', 'support', 'hi', 'hello', 'urgent', 'important', 'fwd:', 're:', 'fw:']
        
        if (len(subject_lower) < 10 or 
            any(subject_lower.startswith(generic) for generic in generic_subjects) or
            subject_lower in generic_subjects):
            
            # For generic subjects, extract just the main question from body
            lines = body.split('\n')
            question_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Stop at signatures (common patterns)
                if any(sig in line.lower() for sig in ['*', 'best regards', 'regards', 'sincerely', 'thanks', 'thank you', '--', '___']):
                    break
                    
                # Stop at very short lines that might be signatures
                if len(line) < 20 and any(char.isdigit() for char in line):
                    break
                    
                question_lines.append(line)
                # Limit to first few lines to avoid signatures
                if len(question_lines) >= 3:
                    break
            
            question_text = ' '.join(question_lines)
        else:
            # Use both subject and body, but limit body to avoid signatures
            body_lines = body.split('\n')[:3]  # First 3 lines only
            question_text = f"{email.subject} {' '.join(body_lines)}".strip()
        
        return question_text.lower().strip()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher."""
        # Break into sentences and check keyword overlap
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        jaccard = intersection / union if union > 0 else 0.0

        # Also use SequenceMatcher for partial string matching
        sequence_ratio = SequenceMatcher(None, text1, text2).ratio()

        # Combine both metrics (60% Jaccard, 40% sequence)
        combined_score = (jaccard * 0.6) + (sequence_ratio * 0.4)

        return combined_score

    def _parse_qa_pairs(self, document_content: str) -> list:
        """Parse Q&A pairs from document content."""
        qa_pairs = []
        lines = document_content.split('\n')
        current_question = None
        current_answer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Q:'):
                # Save previous Q&A pair if exists
                if current_question and current_answer:
                    qa_pairs.append((current_question, '\n'.join(current_answer)))
                
                # Start new question
                current_question = line[2:].strip()  # Remove "Q:" prefix
                current_answer = []
            elif line.startswith('A:') and current_question:
                # Start collecting answer
                current_answer.append(line[2:].strip())  # Remove "A:" prefix
            elif current_question and current_answer:
                # Continue collecting answer
                current_answer.append(line)
        
        # Save last Q&A pair
        if current_question and current_answer:
            qa_pairs.append((current_question, '\n'.join(current_answer)))
        
        return qa_pairs

    def find_response_by_keywords(
        self, email: Email, document_content: str, keywords: list = None
    ) -> Tuple[Optional[str], float]:
        """
        Find response using specific keywords.
        
        Args:
            email: Email object to match
            document_content: Document content to search
            keywords: List of keywords to search for (if None, extracted from email)
        
        Returns:
            Tuple of (response_text, confidence_score)
        """
        if keywords is None:
            # Extract potential keywords from subject
            keywords = [
                word for word in email.subject.lower().split()
                if len(word) > 4  # Filter short words
            ]

        if not keywords:
            return None, 0.0

        # Split document into paragraphs
        paragraphs = document_content.split("\n\n")
        best_match = None
        best_score = 0.0

        for para in paragraphs:
            if not para.strip():
                continue

            # Count keyword matches
            para_lower = para.lower()
            keyword_matches = sum(
                1 for keyword in keywords if keyword in para_lower
            )

            # Calculate score based on keyword density
            if keyword_matches > 0:
                score = keyword_matches / len(keywords)
                if score > best_score:
                    best_score = score
                    best_match = para.strip()

        if best_match and best_score >= self.similarity_threshold:
            logger.info(
                f"Found response match (keyword-based) with score {best_score:.2%}"
            )
            return best_match, best_score
        else:
            return None, 0.0

    def set_threshold(self, threshold: float) -> None:
        """Set similarity threshold."""
        self.similarity_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Similarity threshold set to {self.similarity_threshold}")
