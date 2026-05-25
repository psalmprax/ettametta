import logging
import requests
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class DocumentSkill(OpenClawBaseSkill):
    """
    OpenClaw skill for processing PDF, DOCX, and PPTX files.
    """

    def execute(
        self, type: str = "pdf", action: str = "extract", file_url: str = None, **kwargs
    ) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if not file_url:
            return "⚠️ No file_url provided for Document processing."

        try:
            # Currently, only PDF extraction via Jina is supported in the core DocumentSkill.
            if type.lower() == "pdf" and action.lower() == "extract":
                jina_url = f"https://r.jina.ai/{file_url}"
                resp = requests.get(jina_url, timeout=20)
                if resp.status_code == 200:
                    return f"📄 **PDF Extracted**\n\nPreview:\n{resp.text[:1000]}..."
                return f"⚠️ PDF extraction failed (Status: {resp.status_code})."

            return f"⚠️ Document processing for {type}/{action} is not yet supported. Only type='pdf' with action='extract' is available."
        except Exception as e:
            logger.exception(f"Document Skill Error: {e}")
            return f"⚠️ Document Error: {str(e)}"


document_skill = DocumentSkill()
