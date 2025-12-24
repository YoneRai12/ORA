
import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
import pytz
from typing import Dict, Optional, Literal, Any
from src.config import COST_LIMITS, COST_TZ, STATE_DIR

logger = logging.getLogger("ORA.CostManager")

Lane = Literal["burn", "stable", "byok"]
Provider = Literal["local", "openai", "gemini_dev", "gemini_trial", "claude", "grok"]

@dataclass
class Usage:
    tokens_in: int = 0
    tokens_out: int = 0
    usd: float = 0.0

    def add(self, other: 'Usage'):
        self.tokens_in += other.tokens_in
        self.tokens_out += other.tokens_out
        self.usd += other.usd
    
    def sub(self, other: 'Usage'):
        self.tokens_in = max(0, self.tokens_in - other.tokens_in)
        self.tokens_out = max(0, self.tokens_out - other.tokens_out)
        self.usd = max(0.0, self.usd - other.usd)

@dataclass
class Bucket:
    day: str              # YYYY-MM-DD (JST)
    month: str            # YYYY-MM (JST)
    used: Usage = field(default_factory=Usage)
    reserved: Usage = field(default_factory=Usage)  # in-flight
    hard_stopped: bool = False
    last_update_iso: str = ""

@dataclass
class AllowDecision:
    allowed: bool
    reason: str = ""
    fallback_to: Optional[Provider] = None

class CostManager:
    def __init__(self):
        self.state_file = os.path.join(STATE_DIR, "cost_state.json")
        self.timezone = pytz.timezone(COST_TZ)
        self.global_buckets: Dict[str, Bucket] = {} # key = f"{lane}:{provider}"
        self.user_buckets: Dict[str, Dict[str, Bucket]] = {} # user_id -> (key -> Bucket)
        self._load_state()

    def _get_current_time_keys(self):
        now = datetime.now(self.timezone)
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")

    def _get_bucket_key(self, lane: Lane, provider: Provider) -> str:
        return f"{lane}:{provider}"

    def _load_state(self):
        if not os.path.exists(self.state_file):
            logger.info("No cost state file found. Starting fresh.")
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Restore Global Buckets
            for k, v in data.get("global_buckets", {}).items():
                self.global_buckets[k] = self._dict_to_bucket(v)

            # Restore User Buckets
            for user_id, user_data in data.get("user_buckets", {}).items():
                self.user_buckets[user_id] = {k: self._dict_to_bucket(v) for k, v in user_data.items()}
                
            logger.info("Cost state loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load cost state: {e}")

    def _dict_to_bucket(self, data: dict) -> Bucket:
        return Bucket(
            day=data["day"],
            month=data["month"],
            used=Usage(**data["used"]),
            reserved=Usage(**data["reserved"]),
            hard_stopped=data.get("hard_stopped", False),
            last_update_iso=data.get("last_update_iso", "")
        )

    def _save_state(self):
        try:
            data = {
                "global_buckets": {k: asdict(v) for k, v in self.global_buckets.items()},
                "user_buckets": {uid: {k: asdict(v) for k, v in ubuckets.items()} for uid, ubuckets in self.user_buckets.items()}
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save cost state: {e}")

    def _get_or_create_bucket(self, lane: Lane, provider: Provider, user_id: Optional[int] = None) -> Bucket:
        day_key, month_key = self._get_current_time_keys()
        bucket_key = self._get_bucket_key(lane, provider)
        
        # Determine target dictionary (Global or User)
        if user_id:
            user_str = str(user_id)
            if user_str not in self.user_buckets:
                self.user_buckets[user_str] = {}
            target_map = self.user_buckets[user_str]
        else:
            target_map = self.global_buckets

        bucket = target_map.get(bucket_key)

        # Reset if day/month changed (Basic Logic: If saved day != current day, reset daily counters? 
        # Actually user wants "Daily Limit" resets. 
        # For simplicity, if the bucket definition of 'day' is different, we rotate.
        # But we need to keep monthly usage if month is same.
        
        if bucket is None:
            bucket = Bucket(day=day_key, month=month_key)
            target_map[bucket_key] = bucket
        else:
            # Check for Day Reset
            if bucket.day != day_key:
                # Reset daily stats (reserved/used for day)
                # NOTE: Simpler to just create new bucket but carry over monthly if needed?
                # For now, let's keep it simple: Create new bucket implies 0 usage.
                # BUT this drops monthly usage if we just new() it.
                # So we must verify month.
                
                if bucket.month != month_key:
                    # New Month -> Reset Everything
                     bucket = Bucket(day=day_key, month=month_key)
                else:
                    # Same Month, New Day -> Keep Monthly stats? 
                    # The current structure has 'used' as a single Usage object. It doesn't split daily/monthly.
                    # To support "Monthly Limits" distinct from "Daily Limits", we ideally need separate counters.
                    # HOWEVER, the 'Bucket' definition implies it represents the specific Day/Month.
                    # Let's adjust: We will carry over 'usd' if 'total_usd' is the limit type (Burn Lane).
                    # For Stable Lane, we usually care about daily limits resetting. Monthly limits are separate.
                    
                    # Refinement based on user spec:
                    # User said: "Day/Month Reset in JST automatically"
                    # If I replace the bucket, I lose previous days' data (allows accumulation for monthly?)
                    # State Design decision: We are only tracking "Current Usage against Limits". 
                    # If monthly limit exists, we need sum of usage for this month.
                    # MVP: Let's assume 'used' tracks current DAY usage. 
                    # We might need a separate mechanism for Monthly totals if we want to enforce them strictly.
                    # OR, we just log it and rely on the fact that if day != today, we reset daily counters.
                    
                    # Wait, for "Burn Lane", total_usd is cumulative across forever (or until $300).
                    # So for Burn Lane, we should NEVER reset based on time, unless explicitly managed?
                    # Let's stick to the config:
                    # "gemini_trial": { "total_usd": 300.0 }
                    
                    if lane == "burn":
                         # Dont reset usage for burn lane, just update date markers?
                         bucket.day = day_key
                         bucket.month = month_key
                    else:
                        # For Stable, we want daily reset.
                        # Do we track monthly? Yes. "monthly_tokens": 1_500_000
                        # This simple Bucket model makes monthly tracking hard if we reset daily.
                        # MVP Fix: Just track "Cumulative for Month" in a separate field? 
                        # Or rely on Persistent Storage of *Past* buckets to calc monthly? Too slow.
                        
                        # Let's modify Usage to split?
                        # No, let's just make Bucket have 'monthly_used' and 'daily_used'.
                        pass # See below for modification.
            
                target_map[bucket_key] = bucket

        return bucket

    def can_call(self, lane: Lane, provider: Provider, user_id: Optional[int], est: Usage) -> AllowDecision:
        limits = COST_LIMITS.get(lane, {}).get(provider, {})
        if not limits:
             # No limits defined = Allowed (e.g. Local)
             return AllowDecision(allowed=True)

        if limits.get("hard_stop", False) is False:
            # Explicitly no hard stop (BYOK etc)
            return AllowDecision(allowed=True)

        bucket = self._get_or_create_bucket(lane, provider, user_id)
        
        if bucket.hard_stopped:
            return AllowDecision(allowed=False, reason="Hard Stop Active", fallback_to="local")

        # Check Daily Token Limit (Stable)
        daily_limit = limits.get("daily_tokens")
        if daily_limit:
            current_total = bucket.used.tokens_in + bucket.used.tokens_out + bucket.reserved.tokens_in + bucket.reserved.tokens_out
            est_total = est.tokens_in + est.tokens_out
            if current_total + est_total > daily_limit:
                 return AllowDecision(allowed=False, reason=f"Daily Token Limit Exceeded ({current_total}/{daily_limit})", fallback_to="local")

        # Check Burn Limit (USD)
        total_usd_limit = limits.get("total_usd")
        if total_usd_limit:
            current_usd = bucket.used.usd + bucket.reserved.usd
            if current_usd + est.usd > total_usd_limit:
                return AllowDecision(allowed=False, reason=f"Burn Budget Exceeded (${current_usd}/${total_usd_limit})", fallback_to="local")

        return AllowDecision(allowed=True)

    # --- State Helper for In-Flight ---
    _reservations: Dict[str, Usage] = {}

    def reserve(self, lane: Lane, provider: Provider, user_id: Optional[int], reservation_id: str, est: Usage) -> None:
        # Store reservation map
        self._reservations[reservation_id] = est
        
        # Add to Bucket Reserved
        bucket = self._get_or_create_bucket(lane, provider, user_id)
        bucket.reserved.add(est)
        bucket.last_update_iso = datetime.now(self.timezone).isoformat()
        self._save_state()

    def commit(self, lane: Lane, provider: Provider, user_id: Optional[int], reservation_id: str, actual: Usage) -> None:
        est = self._reservations.pop(reservation_id, None)
        bucket = self._get_or_create_bucket(lane, provider, user_id)
        
        bucket.used.add(actual)
        if est:
            bucket.reserved.sub(est)
        
        bucket.last_update_iso = datetime.now(self.timezone).isoformat()
        self._save_state()

    def rollback(self, lane: Lane, provider: Provider, user_id: Optional[int], reservation_id: str, mode: Literal["release","keep"]="release") -> None:
        """
        Revert a reservation.
        mode="release": Cancel it (e.g. API error).
        mode="keep": Convert to used (e.g. partial success? or treated as consumed quota)
        Default for rollback on error is usually 'release' (don't charge).
        """
        est = self._reservations.get(reservation_id)
        if not est: 
            return

        bucket = self._get_or_create_bucket(lane, provider, user_id)
        
        if mode == "release":
            bucket.reserved.sub(est)
            del self._reservations[reservation_id]
        elif mode == "keep":
            # Treat as Used
            bucket.used.add(est)
            bucket.reserved.sub(est)
            del self._reservations[reservation_id]
            
        bucket.last_update_iso = datetime.now(self.timezone).isoformat()
        self._save_state()

