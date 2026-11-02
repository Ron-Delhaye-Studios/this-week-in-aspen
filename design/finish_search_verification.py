"""Owner-supplied Search Console tag belongs here; never invent its token."""
from bs4 import Comment

SLOT = ' Google Search Console verification — awaiting MASTER INDY token. Add the supplied google-site-verification meta tag here; do not invent a value. '


def apply(doc, path, root):
    if not doc.head or doc.head.select_one('meta[name="google-site-verification"]'):
        return
    if not any(isinstance(node, Comment) and 'Google Search Console verification' in node for node in doc.head.children):
        doc.head.append(Comment(SLOT))
