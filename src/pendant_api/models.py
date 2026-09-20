"""The shared, explicit catalogue of local speech models.

Download sizes are rounded estimates, not RAM requirements or progress totals.
Keeping IDs allowlisted prevents API callers from selecting arbitrary Hub repos.
"""

MODEL_CATALOGUE = (
    {"id": "large-v3-turbo", "label": "Whisper Large v3 Turbo", "download_mb": 1620,
     "description": "Recommended for this workflow. Strong multilingual recognition with a faster decoder than Large v3.", "recommended": True},
    {"id": "large-v3", "label": "Whisper Large v3", "download_mb": 3100,
     "description": "Full multilingual model. A useful quality comparison; substantially slower on a CPU."},
    {"id": "medium.en", "label": "Whisper Medium · English", "download_mb": 1530,
     "description": "Larger English-only model. More demanding than Small."},
    {"id": "medium", "label": "Whisper Medium · Multilingual", "download_mb": 1530,
     "description": "Multilingual recognition with a smaller download than Large v3."},
    {"id": "small.en", "label": "Whisper Small · English", "download_mb": 490,
     "description": "A practical English model for shorter CPU processing times."},
    {"id": "small", "label": "Whisper Small · Multilingual", "download_mb": 490,
     "description": "A lighter multilingual option for everyday testing."},
    {"id": "base.en", "label": "Whisper Base · English", "download_mb": 150,
     "description": "Quick setup and a useful first check. Less reliable on difficult speech."},
    {"id": "base", "label": "Whisper Base · Multilingual", "download_mb": 150,
     "description": "Quick multilingual checks with a small download."},
    {"id": "tiny.en", "label": "Whisper Tiny · English", "download_mb": 80,
     "description": "The smallest download. Best for checking the pipeline, rather than transcript quality."},
)
MODELS = tuple(model["id"] for model in MODEL_CATALOGUE)
DEFAULT_MODEL = "base.en"  # Preserve existing installations and API clients.
RECOMMENDED_MODEL = "large-v3-turbo"
