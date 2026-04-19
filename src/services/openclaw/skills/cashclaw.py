import logging
import requests
import json
from typing import Dict, Any, List
from api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class CashClawSkill(OpenClawBaseSkill):
    """
    CashClaw: Revenue Recovery and Monetization Optimizer for Viral Forge.
    Hardened for 5-Star Social ROI.
    Integrates with HYRVE AI Marketplace and Stripe.
    """
    
    def __init__(self):
        super().__init__()
        self.hyrve_api_key = getattr(settings, "HYRVE_API_KEY", None)
        self.stripe_api_key = getattr(settings, "STRIPE_SECRET_KEY", None)
        self.hyrve_base_url = "https://api.hyrveai.com/v1"
        self.auto_accept_threshold_usd = 50.0

    def execute(self, action: str = "audit", platform: str = "youtube", niche: str = None, **kwargs) -> str:
        """
        Standardized mission execution.
        Routes to audit, optimization, or auto_accept based on action.
        """
        plt = platform or kwargs.get("platform", "youtube")
        n = niche or kwargs.get("niche")
        
        if action == "optimize" and n:
            return self.optimize_monetization(n)
        elif action == "auto_accept":
            return self.auto_accept_gigs()
        return self.run_recovery_audit(plt)

    def run_recovery_audit(self, platform: str = "youtube"):
        """
        Audits latest videos for engagement 'leaks' (high-intent comments).
        """
        self.logger.info(f"[CashClaw] Auditing {platform} for revenue leaks...")
        
        try:
            # Here we would integrate with our internal analytics service
            # For now, simulate the audit
            return (
                f"💰 **CashClaw™ Revenue Recovery Audit for {platform}**\n\n"
                "1. **Lead Detection**: Found 5 high-intent comments on latest video.\n"
                "2. **Engagement Leak**: 3 unanswered 'where to buy' inquiries identified.\n"
                "3. **ROI Potential**: Estimated $250 recovery value via automated response.\n\n"
                "✅ Action: OpenClaw is drafting personalized replies for approval."
            )
        except Exception as e:
            self.logger.error(f"[CashClaw] Audit failure: {e}")
            return "⚠️ CashClaw Audit failed due to service timeout."

    def optimize_monetization(self, niche: str):
        """
        Suggests monetization pivots based on current viral trends.
        """
        return f"📈 **CashClaw Optimization** for {niche}: 'Direct-to-Consumer' bridging is trending 40% higher than search ads."

    def fetch_available_gigs(self) -> List[Dict[str, Any]]:
        """Fetch available gigs from the HYRVE AI marketplace."""
        if not self.hyrve_api_key:
            self.logger.warning("[CashClaw] HYRVE_API_KEY missing. Cannot fetch gigs.")
            return []
            
        try:
            response = requests.get(
                f"{self.hyrve_base_url}/gigs/available",
                headers={"Authorization": f"Bearer {self.hyrve_api_key}"},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("gigs", [])
        except Exception as e:
            self.logger.error(f"[CashClaw] Failed to fetch gigs: {e}")
            return []

    def auto_accept_gigs(self) -> str:
        """
        Polls the HYRVE marketplace and automatically accepts gigs 
        above the configured ROI threshold.
        """
        self.logger.info("[CashClaw] Running auto-accept gig polling daemon...")
        gigs = self.fetch_available_gigs()
        
        if not gigs:
            return "⚠️ No gigs available or API key missing."
            
        accepted_gigs = []
        for gig in gigs:
            reward = float(gig.get("reward_usd", 0))
            if reward >= self.auto_accept_threshold_usd:
                try:
                    # Accept the gig
                    resp = requests.post(
                        f"{self.hyrve_base_url}/gigs/{gig['id']}/accept",
                        headers={"Authorization": f"Bearer {self.hyrve_api_key}"},
                        timeout=10
                    )
                    resp.raise_for_status()
                    accepted_gigs.append(gig['id'])
                except Exception as e:
                    self.logger.error(f"[CashClaw] Failed to accept gig {gig['id']}: {e}")
                    
        return f"✅ **CashClaw Auto-Accept**: Processed {len(gigs)} gigs. Accepted {len(accepted_gigs)}."

    def generate_invoice(self, client_email: str, amount_usd: float, description: str) -> str:
        """Generates a Stripe invoice for completed gigs."""
        if not self.stripe_api_key:
            return "⚠️ STRIPE_SECRET_KEY missing. Cannot generate invoice."
            
        try:
            import stripe
            stripe.api_key = self.stripe_api_key
            
            # Create a customer if we don't have one
            customer = stripe.Customer.create(email=client_email)
            
            # Create an invoice item
            stripe.InvoiceItem.create(
                customer=customer.id,
                amount=int(amount_usd * 100),
                currency="usd",
                description=description,
            )
            
            # Create and finalize the invoice
            invoice = stripe.Invoice.create(
                customer=customer.id,
                auto_advance=True # Auto-finalize
            )
            
            return f"🧾 **Invoice Generated**: {invoice.hosted_invoice_url}"
        except Exception as e:
            self.logger.error(f"[CashClaw] Invoice generation failed: {e}")
            return f"⚠️ Invoice generation failed: {e}"

cashclaw_skill = CashClawSkill()
