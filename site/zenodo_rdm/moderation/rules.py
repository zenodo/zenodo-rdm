import re
from urllib.parse import urlparse

from flask import current_app

# Moderation Scores
SPAM_LINK_SCORE = 8
HAM_LINK_SCORE = -3
EXCESS_LINKS_SCORE = 5
SPAM_EMOJI_SCORE = 5
SPAM_FILES_SCORE = 2
HAM_FILES_SCORE = -5
UNVERIFIED_USER_SCORE = 10
VERIFIED_USER_SCORE = -10


class DomainTree:
    def __init__(self):
        self.tree = {}
        self.score = 0
        self.initialize_links(
            current_app.config.get("CONTENT_MODERATION_BANNED_LINKS", []), "banned"
        )
        self.initialize_links(
            current_app.config.get("CONTENT_MODERATION_SAFE_LINKS", []), "safe"
        )

    def add_domain(self, domain, status):
        """Add a domain to the tree with its status: 'banned' or 'safe'."""
        parts = domain.strip(".").split(".")
        current = self.tree
        for part in parts:
            current = current.setdefault(part, {})
        current["status"] = status

    def initialize_links(self, links, status):
        """Helper method to add multiple links to the domain tree with a given status."""
        for domain in links:
            self.add_domain(domain, status)

    def get_status(self, domain_parts):
        """Retrieve the status of a domain"""
        current = self.tree
        for part in domain_parts:
            if part in current:
                current = current[part]
                if "status" in current:
                    return current["status"]
            else:
                break
        return None

    def score_links(self, metadata):
        """Calculate the score based on the domains found in the metadata links."""
        description_links = self.extract_links(str(metadata.get("description", "")))

        if len(description_links) > 5:
            self.score += EXCESS_LINKS_SCORE

        extracted_links = self.extract_links(str(metadata))

        for link in extracted_links:
            domain_parts = self.extract_domain(link)
            status = self.get_status(domain_parts)
            if status == "banned":
                self.score += SPAM_LINK_SCORE
            elif status == "safe":
                self.score += HAM_LINK_SCORE
        return self.score

    @staticmethod
    def extract_links(metadata):
        """Extract unique URLs from metadata using regex."""
        url_pattern = re.compile(
            r'href=["\']?([^"\'>]+)|\b(https?://[^\s\'"<>,]+|www\.[^\s\'"<>,]+)',
        )

        links = []
        for match in url_pattern.findall(metadata):
            for url in match:
                if url:
                    links.append(url)

        return links

    @staticmethod
    def extract_domain(url):
        """Extract and reverse domain parts from a given URL."""
        pattern = r"^(?:https?://)?(?:www\.)?([^/]+)"
        match = re.search(pattern, url)
        if match:
            domain = match.group(1)
            domain_parts = domain.split(".")
            return domain_parts[::-1]
        return None


# Utility Functions


def extract_emojis(text):
    """Extract all emojis from text using a regex pattern."""
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        "\U00002700-\U000027BF"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "]+",
        flags=re.UNICODE,
    )
    return EMOJI_PATTERN.findall(text)


# Moderation Rule Functions


def links_rule(identity, draft=None, record=None):
    """Calculate a moderation score based on links found in record metadata."""
    domain_tree = DomainTree()
    return domain_tree.score_links(record.metadata)


def text_sanitization_rule(identity, draft=None, record=None):
    """Calculate a score for excessive emoji usage in metadata text."""
    record_text = " ".join(map(str, record.metadata.values()))
    return SPAM_EMOJI_SCORE if len(extract_emojis(record_text)) > 3 else 0


def verified_user_rule(identity, draft=None, record=None):
    """Adjust moderation score based on the verification status of the user."""
    is_verified = (
        getattr(record.parent, "is_verified", None)
        if hasattr(record, "parent")
        else getattr(record, "is_verified", False)
    )
    return UNVERIFIED_USER_SCORE if not is_verified else VERIFIED_USER_SCORE


def files_rule(identity, draft=None, record=None):
    """Calculate score based on the number, size, and type of files associated with the record."""
    score = 0
    files_count = record.files.count
    file_size_threshold = current_app.config.get("RDM_CONTENT_MODERATION_FILE_SIZE")
    data_size = record.files.total_bytes
    exts = {filename.split(".")[-1].lower() for filename in record.files.entries.keys()}

    if (
        files_count == 1
        and data_size < file_size_threshold
        and len(exts.intersection(current_app.config.get("SPAM_FILE_EXTS"))) > 0
    ):
        score += SPAM_FILES_SCORE

    if files_count > 3 or data_size > file_size_threshold:
        score += HAM_FILES_SCORE

    return score
