"""
Common modules for spam detection system
"""

from .excluded_sites import excluded_sites_manager
from .filter_registry import registry, register_filter
from .phone_shopee_detector import contains_vietnam_phone_or_shopee_link
from .real_estate_classifier import check_real_estate_spam
from .bank_spam_classifier import check_bank_spam

__all__ = [
    'excluded_sites_manager',
    'registry',
    'register_filter',
    'contains_vietnam_phone_or_shopee_link',
    'check_real_estate_spam',
    'check_bank_spam',
]
