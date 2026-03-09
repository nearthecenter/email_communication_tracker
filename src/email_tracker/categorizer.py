"""Email categorization service using AI."""

import logging
from typing import Optional
from .models import Email

logger = logging.getLogger(__name__)


class EmailCategorizer:
    """Categorizes emails using AI analysis."""

    # Predefined categories
    CATEGORIES = {
        "Sales & Offers": ["product", "sale", "discount", "offer", "promotion", "deal", "buy", "purchase"],
        "Support & Help": ["help", "support", "issue", "problem", "error", "fix", "bug", "broken"],
        "Administrative": ["meeting", "schedule", "calendar", "appointment", "confirm", "registration"],
        "Marketing & Newsletter": ["newsletter", "update", "news", "webinar", "event", "announce"],
        "Financial": ["invoice", "payment", "receipt", "billing", "transaction", "refund", "quote"],
        "HR & Recruitment": ["job", "interview", "hire", "resume", "position", "apply", "candidate"],
        "General Inquiry": ["question", "info", "detail", "explain", "clarify", "understand"],
        "System & Notification": ["notification", "alert", "system", "status", "confirm"],
    }

    def __init__(self):
        """Initialize categorizer."""
        self.categories = self.CATEGORIES

    def categorize(self, email: Email) -> str:
        """
        Categorize email based on subject and body content.
        Uses keyword matching for fast categorization.
        """
        text_to_analyze = f"{email.subject.lower()} {email.body.lower()}"

        # Count category keyword matches
        category_scores = {}
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"Email categorized as: {best_category}")
            return best_category
        else:
            logger.info("Email categorized as: General Inquiry (default)")
            return "General Inquiry"

    def add_custom_category(self, category_name: str, keywords: list) -> None:
        """Add a custom category with keywords."""
        self.categories[category_name] = keywords
        logger.info(f"Added custom category: {category_name}")

    def get_categories(self) -> dict:
        """Get all categories and their keywords."""
        return self.categories
