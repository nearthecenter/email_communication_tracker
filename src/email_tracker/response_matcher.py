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
        logger.info(f"Extracted question text: {repr(question_text)}")

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
            # Log best score seen even when below threshold
            if qa_pairs:
                all_scores = [(q, self._calculate_similarity(question_text, q.lower().strip())) for q, _ in qa_pairs]
                best = max(all_scores, key=lambda x: x[1])
                logger.info(f"No matching Q&A found (best score: {best[1]:.2%} for '{best[0][:60]}')")
            else:
                logger.info("No matching Q&A found")
            return None, 0.0

    def _extract_question_text(self, email: Email) -> str:
        """Extract the main question text from an email, filtering out signatures and noise."""
        body = email.body.strip()

        # Always extract the meaningful content from the body first.
        # The subject alone is unreliable (missing, generic, or unrelated),
        # so we prioritise the body and only fall back to the subject when
        # the body yields nothing useful.
        lines = body.split('\n')
        question_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()
            short_closings = {'thanks', 'thank you'}
            hard_sigs = ['best regards', 'regards,', 'sincerely,', '--', '___']
            is_separator = all(c == '*' for c in line.replace(' ', ''))
            # Gmail quote header: "On <date>, <name> wrote:" — stop before quoted reply
            is_quote_header = (line_lower.startswith('on ') and line_lower.endswith('wrote:'))
            is_hard_sig = is_separator or is_quote_header or any(sig in line_lower for sig in hard_sigs)
            is_short_closing = (
                any(sig in line_lower for sig in short_closings)
                and len(line) <= 50
            )
            if is_hard_sig or is_short_closing:
                break

            # Stop at very short lines that look like contact/phone numbers
            if len(line) < 20 and any(char.isdigit() for char in line):
                break

            question_lines.append(line)
            if len(question_lines) >= 3:
                break

        question_text = ' '.join(question_lines)

        # Fallback: if body gave nothing, use the subject
        if not question_text.strip():
            question_text = email.subject
        
        return self._strip_noise_words(question_text.lower().strip())

    # Common greeting/closing phrases that add noise to similarity scoring
    _NOISE_PHRASES = [
        'hello!', 'hello', 'hi!', 'hi', 'good morning', 'good afternoon',
        'good evening', 'good day', 'dear sir', 'dear ma\'am', 'dear sir or ma\'am',
        'i want to ask', 'i would like to ask', 'i would like to inquire',
        'i wanted to ask', 'may i ask', 'can i ask', 'i just want to ask',
        'i just wanted to ask', 'thank you!', 'thank you', 'thanks!', 'thanks',
        'i hope this finds you well', 'i hope you are doing well',
    ]

    def _strip_noise_words(self, text: str) -> str:
        """Remove common greeting/closing phrases that dilute similarity scores."""
        import re
        for phrase in self._NOISE_PHRASES:
            # Match phrase as a whole unit (with optional punctuation around it)
            text = re.sub(r'\b' + re.escape(phrase) + r'\b[,.]?\s*', '', text, flags=re.IGNORECASE)
        return text.strip()

    # Stop-words that carry little meaning for FAQ matching
    _STOP_WORDS = {
        'a', 'an', 'the', 'is', 'it', 'in', 'of', 'to', 'for', 'and',
        'or', 'do', 'if', 'my', 'me', 'we', 'i', 'be', 'at', 'on',
        'with', 'this', 'that', 'are', 'was', 'will', 'what', 'how',
        'why', 'when', 'where', 'who', 'get', 'have', 'has', 'been',
        'not', 'no', 'its', 'by', 'from', 'as', 'up', 'so',
        # common filler/polite words that add noise
        'please', 'kindly', 'just', 'also', 'like', 'want', 'need',
        'ask', 'know', 'thank', 'thanks', 'help', 'Dear',
        # common verbs that don't help matching
        'show', 'shows', 'send', 'try', 'use', 'used', 'goes', 'went',
    }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.

        Uses keyword coverage (how much of the shorter text's meaningful words
        appear in the longer text) rather than Jaccard, so short email queries
        are not penalised against longer FAQ questions.
        """
        def meaningful_words(text):
            return set(
                w.strip('!?,.:;()[]\'\"')
                for w in text.lower().split()
                if w.strip('!?,.:;()[]\'\"') and
                   w.strip('!?,.:;()[]\'\"') not in self._STOP_WORDS and
                   len(w.strip('!?,.:;()[]\'\"')) > 2
            )

        words1 = meaningful_words(text1)
        words2 = meaningful_words(text2)

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        # Coverage: what fraction of the EMAIL's (text1) keywords appear in the FAQ question.
        # Using text1 (email) as denominator avoids short FAQs with few keywords
        # falsely dominating over more specific FAQs.
        coverage = intersection / len(words1)

        # SequenceMatcher for partial string matching
        sequence_ratio = SequenceMatcher(None, text1, text2).ratio()

        # 65% coverage, 35% sequence
        return (coverage * 0.65) + (sequence_ratio * 0.35)

    def _parse_qa_pairs(self, document_content: str) -> list:
        """Parse Q&A pairs from document content.

        Handles two formats:
        1. Q and A on separate lines (standard)
        2. Q and A on the same line: "Q: question?A: answer"
        """
        import re
        qa_pairs = []
        lines = document_content.split('\n')
        current_question = None
        current_answer = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Handle case where Q: and A: are on the same line
            if (line.startswith('Q:') or line.startswith('Q.')) and 'A:' in line:
                # Save previous pair
                if current_question and current_answer:
                    qa_pairs.append((current_question, '\n'.join(current_answer)))
                # Split on A: to separate question from answer
                parts = re.split(r'A:', line, maxsplit=1)
                current_question = parts[0][2:].strip()
                current_answer = [parts[1].strip()] if len(parts) > 1 else []
                # Save immediately if we have both
                if current_question and current_answer:
                    qa_pairs.append((current_question, '\n'.join(current_answer)))
                    current_question = None
                    current_answer = []
            elif line.startswith('Q:') or line.startswith('Q.'):
                # Save previous Q&A pair if exists
                if current_question and current_answer:
                    qa_pairs.append((current_question, '\n'.join(current_answer)))
                current_question = line[2:].strip()
                current_answer = []
            elif line.startswith('A:') and current_question:
                current_answer.append(line[2:].strip())
            elif current_question and current_answer:
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
