"""
Credit System Database Models for Viral Forge
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import uuid


class CreditPackageDB(Base):
    """Predefined credit packages for purchase"""
    __tablename__ = "credit_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # e.g., "Starter", "Pro", "Enterprise"
    credits = Column(Integer)  # Number of credits
    price_cents = Column(Integer)  # Price in cents
    stripe_price_id = Column(String, nullable=True)  # Stripe price ID
    is_active = Column(Boolean, default=True)
    features = Column(JSON, default=[])  # Bonus features
    created_at = Column(DateTime, default=datetime.utcnow)


class UserCreditDB(Base):
    """User's credit balance and history"""
    __tablename__ = "user_credits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    balance = Column(Integer, default=0)  # Available credits
    lifetime_purchased = Column(Integer, default=0)  # Total credits ever purchased
    lifetime_earned = Column(Integer, default=0)  # Total credits earned (referrals, etc.)
    lifetime_spent = Column(Integer, default=0)  # Total credits spent
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditTransactionDB(Base):
    """Credit purchase/deduction history"""
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Integer)  # Positive for purchase/earn, negative for spend
    balance_after = Column(Integer)  # Balance after transaction
    transaction_type = Column(String)  # purchase, earned, spent, bonus, refund, expiration
    description = Column(String, nullable=True)
    stripe_payment_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)  # For subscription credits
    reference_id = Column(String, nullable=True)  # For linking to related entities
    created_at = Column(DateTime, default=datetime.utcnow)


class ReferralDB(Base):
    """Referral tracking"""
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), index=True)  # Who referred
    referred_id = Column(Integer, ForeignKey("users.id"), index=True)  # Who was referred
    referral_code = Column(String, unique=True, index=True)
    status = Column(String, default="pending")  # pending, completed, reward_claimed
    reward_credits = Column(Integer, default=0)
    reward_claimed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CreditUsageRuleDB(Base):
    """Defines how credits are consumed for different actions"""
    __tablename__ = "credit_usage_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, unique=True, index=True)  # e.g., "video_generation", "voice_clone"
    credits_required = Column(Integer)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    tier_required = Column(String, nullable=True)  # Minimum tier required


class SubscriptionCreditDB(Base):
    """Monthly credits included with subscription"""
    __tablename__ = "subscription_credits"
    
    id = Column(Integer, primary_key=True, index=True)
    tier = Column(String, unique=True, index=True)  # free, creator, empire, sovereign, studio
    monthly_credits = Column(Integer)
    rollover_enabled = Column(Boolean, default=False)
    max_rollover = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
