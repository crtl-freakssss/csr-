import re


class PromptSanitizer:
    """Sanitizes untrusted proposal text to defend against prompt injection (Technical Contract Section 70)."""

    DANGEROUS_TAG_PATTERNS = [
        (r"</?untrusted_proposal_document[^>]*>", lambda m: m.group(0).replace("<", "&lt;").replace(">", "&gt;")),
        (r"</?system[^>]*>", lambda m: m.group(0).replace("<", "&lt;").replace(">", "&gt;")),
        (r"</?document_data[^>]*>", lambda m: m.group(0).replace("<", "&lt;").replace(">", "&gt;")),
        (r"\[/?INST\]", lambda m: m.group(0).replace("[", "&#91;").replace("]", "&#93;")),
        (r"<\|im_start\|>", "&lt;|im_start|&gt;"),
        (r"<\|im_end\|>", "&lt;|im_end|&gt;"),
        (r"<\|system\|>", "&lt;|system|&gt;"),
        (r"<\|user\|>", "&lt;|user|&gt;"),
        (r"<\|assistant\|>", "&lt;|assistant|&gt;"),
    ]

    def sanitize_untrusted_text(self, text: str) -> str:
        """Neutralize potential prompt injection delimiters and format escape tokens."""
        if not text:
            return ""

        sanitized = text
        for pattern, replacement in self.DANGEROUS_TAG_PATTERNS:
            if callable(replacement):
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            else:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    def wrap_in_document_boundary(self, text: str) -> str:
        """Sanitize text and encapsulate inside unambiguous structural untrusted data markers."""
        sanitized = self.sanitize_untrusted_text(text)
        return f"<untrusted_proposal_document>\n{sanitized}\n</untrusted_proposal_document>"
