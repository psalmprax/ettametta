import logging
import random
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy import select
from .base import BaseMonetizationStrategy
from src.api.utils.database import async_session_factory
from src.api.utils.models import SystemSettings

class CryptoStrategy(BaseMonetizationStrategy):
    """
    Crypto/Donations strategy - Accept crypto tips or donations
    """
    
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        """
        Fetches crypto wallet addresses from database configuration.
        Returns available crypto wallets for donations/tips.
        """
        async with async_session_factory() as db:
            # Check for configured crypto wallets
            stmt = select(SystemSettings).filter(SystemSettings.key == "crypto_wallets")
            result = await db.execute(stmt)
            wallets_setting = result.scalar_one_or_none()
            
            if not wallets_setting or not wallets_setting.value:
                logging.warning("[CryptoStrategy] No crypto wallets configured. Set 'crypto_wallets' in settings (format: BTC:addr,ETH:addr).")
                return []
            
            # Parse wallets (format: BTC:addr,ETH:addr,USDT:addr)
            assets = []
            wallet_str = wallets_setting.value
            
            if "BTC" in wallet_str.upper():
                btc_addr = self._extract_wallet(wallet_str, "BTC")
                if btc_addr:
                    assets.append({
                        "id": "btc_wallet",
                        "name": "Bitcoin",
                        "symbol": "BTC",
                        "url": f"bitcoin:{btc_addr}",
                        "address": btc_addr,
                        "cta_text": "Send BTC Tip",
                        "type": "crypto"
                    })
            
            if "ETH" in wallet_str.upper():
                eth_addr = self._extract_wallet(wallet_str, "ETH")
                if eth_addr:
                    assets.append({
                        "id": "eth_wallet",
                        "name": "Ethereum", 
                        "symbol": "ETH",
                        "url": f"ethereum:{eth_addr}",
                        "address": eth_addr,
                        "cta_text": "Send ETH Tip",
                        "type": "crypto"
                    })
            
            if "USDT" in wallet_str.upper():
                usdt_addr = self._extract_wallet(wallet_str, "USDT")
                if usdt_addr:
                    assets.append({
                        "id": "usdt_wallet",
                        "name": "Tether (USDT)",
                        "symbol": "USDT",
                        "url": usdt_addr,
                        "address": usdt_addr,
                        "cta_text": "Support via USDT",
                        "type": "crypto"
                    })
            
            # Add generic donation link if configured
            stmt_donation = select(SystemSettings).filter(SystemSettings.key == "donation_link")
            result_donation = await db.execute(stmt_donation)
            donation_setting = result_donation.scalar_one_or_none()
            
            if donation_setting and donation_setting.value:
                assets.append({
                    "id": "donation_link",
                    "name": "Support via PayPal/Donation",
                    "url": donation_setting.value,
                    "cta_text": "Donate Now",
                    "type": "donation"
                })
            
            if not assets:
                logging.warning(f"[CryptoStrategy] Could not parse crypto wallets from: {wallets_setting.value}")
                return []
            
            return assets
    
    async def validate_address(self, address: str, symbol: str) -> bool:
        """
        Validates a crypto address using regex or public APIs.
        """
        import re
        if symbol.upper() == "BTC":
            return bool(re.match(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[ac-hj-np-z02-9]{11,71}$", address))
        elif symbol.upper() == "ETH" or symbol.upper() == "USDT":
            return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))
        return len(address) > 20

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=False
    )
    async def get_balance(self, address: str, symbol: str) -> float | None:
        """
        Fetches real balance from public blockchain APIs.
        """
        import httpx
        try:
            if symbol.upper() == "BTC":
                url = f"https://blockchain.info/q/addressbalance/{address}"
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        return float(resp.text) / 10**8 # Satoshi to BTC
            elif symbol.upper() == "ETH":
                # Etherscan requires API key for high volume, but has some public endpoints
                url = f"https://api.blockcypher.com/v1/eth/main/addrs/{address}/balance"
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        return resp.json().get("balance", 0) / 10**18
        except Exception as e:
            logging.exception(f"[CryptoStrategy] Balance check failed for {symbol}: {e}")
        return None

    def _extract_wallet(self, wallet_str: str, symbol: str) -> str:
        """Extract wallet address for a given symbol"""
        try:
            parts = wallet_str.split(",")
            for part in parts:
                if symbol.upper() in part.upper():
                    addr = part.split(":")[-1].strip()
                    if addr and len(addr) > 10:
                        return addr
        except Exception:
            pass
        return None

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for crypto tips/donations.
        """
        assets = await self.get_assets(niche)
        
        if assets:
            crypto_asset = next((a for a in assets if a.get("type") == "crypto"), assets[0])
            if crypto_asset.get("type") == "crypto":
                symbol = crypto_asset.get("symbol", "crypto")
                address = crypto_asset.get("address", "")[:10] + "..."
                options = [
                    f"Loved this content? Send a tip in {symbol}! \n📱 {address}",
                    f"Support this channel with {symbol}! Every bit helps: \n📱 {address}",
                    f"Appreciate the content? Drop a {symbol} tip: \n📱 {address}",
                    f"Help us create more content! {symbol} donations: \n📱 {address}"
                ]
            else:
                # Donation link
                url = crypto_asset.get("url", "")
                if not url:
                    logging.warning(f"[CryptoStrategy] No donation URL configured for niche: {niche}")
                    return ""
                options = [
                    f"Enjoyed this? Support us here: \n🔗 {url}",
                    f"Help keep this channel going! Donate: \n🔗 {url}",
                    f"Any support helps! Link in bio: \n🔗 {url}"
                ]
        else:
            options = [
                "Enjoyed this? Support the channel! Link in bio 💜",
                "Help us create more content! Every bit helps 💜",
                "Like what you see? Support us! Link below 💜"
            ]
        
        return random.choice(options)
