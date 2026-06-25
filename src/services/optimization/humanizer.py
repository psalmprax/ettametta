import re

class TextHumanizer:
    # A mapping of common AI slop patterns to natural, human alternatives
    SLOP_PATTERNS = {
        r"\bLeveraging\b": "Using",
        r"\bleveraging\b": "using",
        r"\bLeverage\b": "Use",
        r"\bleverage\b": "use",
        r"\bDelving\b": "Digging",
        r"\bdelving\b": "digging",
        r"\bDelve\b": "Dig",
        r"\bdelve\b": "dig",
        r"\bTestament\b": "Proof",
        r"\btestament\b": "proof",
        r"\bVibrant\b": "Lively",
        r"\bvibrant\b": "lively",
        r"\bLandscape\b": "Environment",
        r"\blandscape\b": "environment",
        r"\bPivotal\b": "Key",
        r"\bpivotal\b": "key",
        r"\bTapestry\b": "Mix",
        r"\btapestry\b": "mix",
        r"\bGame-changer\b": "Big deal",
        r"\bgame-changer\b": "big deal",
        r"\bRevolutionize\b": "Change",
        r"\brevolutionize\b": "change",
        r"\bMultifaceted\b": "Varied",
        r"\bmultifaceted\b": "varied",
        r"\bMoreover\b": "Also",
        r"\bmoreover\b": "also",
        r"\bFurthermore\b": "Also",
        r"\bfurthermore\b": "also",
        r"\bRealm\b": "Area",
        r"\brealm\b": "area",
        r"\bDemystify\b": "Explain",
        r"\bdemystify\b": "explain",
        r"\bBeacon\b": "Guide",
        r"\bbeacon\b": "guide",
        r"\bTreasure trove\b": "Goldmine",
        r"\btreasure trove\b": "goldmine",
        r"\bTreasure Trove\b": "Goldmine",
        r"\bUnderscores\b": "Shows",
        r"\bunderscores\b": "shows",
        r"\bElevate\b": "Raise",
        r"\belevate\b": "raise",
        r"\bFoster\b": "Build",
        r"\bfoster\b": "build",
        r"\bStreamline\b": "Simplify",
        r"\bstreamline\b": "simplify",
        r"\bNestled\b": "Located",
        r"\bnestled\b": "located",
        r"\bWhispers\b": "Rumors",
        r"\bwhispers\b": "rumors",
        r"\b[iI]t is important to note that\s*": "",
        r"\bPlethora\b": "Lot",
        r"\bplethora\b": "lot",
        r"\bUtmost\b": "Greatest",
        r"\butmost\b": "greatest",
        r"\bBespoke\b": "Custom",
        r"\bbespoke\b": "custom",
        r"\bCutting-edge\b": "Modern",
        r"\bcutting-edge\b": "modern",
        r"\bCutting-Edge\b": "Modern",
        r"\bRobust\b": "Reliable",
        r"\brobust\b": "reliable",
    }


    @classmethod
    def humanize(cls, text: str) -> str:
        if not text:
            return text
        
        for pattern, replacement in cls.SLOP_PATTERNS.items():
            text = re.sub(pattern, replacement, text)
            
        # Clean up any resulting double spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

base_humanizer = TextHumanizer()


