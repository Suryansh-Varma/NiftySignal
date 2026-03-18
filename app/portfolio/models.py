"""
Data models for portfolio tracking.

For now using simple JSON/CSV storage. Can be upgraded to PostgreSQL/MongoDB later.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path


@dataclass
class Holding:
    """Represents a single stock holding in a portfolio."""
    symbol: str  # e.g., "RELIANCE.NS"
    shares: float  # Number of shares
    avg_buy_price: float  # Average purchase price
    purchase_date: Optional[str] = None  # YYYY-MM-DD format
    notes: str = ""
    
    @property
    def total_invested(self) -> float:
        """Total amount invested in this holding."""
        return self.shares * self.avg_buy_price
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "symbol": self.symbol,
            "shares": self.shares,
            "avg_buy_price": self.avg_buy_price,
            "purchase_date": self.purchase_date,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Holding':
        """Create Holding from dictionary."""
        return cls(**data)


@dataclass
class Portfolio:
    """Represents a user's complete portfolio."""
    user_id: str
    name: str
    holdings: List[Holding] = field(default_factory=list)
    cash_balance: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    @property
    def total_invested(self) -> float:
        """Total amount invested across all holdings."""
        return sum(h.total_invested for h in self.holdings) + self.cash_balance
    
    @property
    def symbols(self) -> List[str]:
        """List of all symbols in portfolio."""
        return [h.symbol for h in self.holdings]
    
    def add_holding(self, holding: Holding):
        """Add a new holding or update existing one."""
        # Check if symbol already exists
        existing = next((h for h in self.holdings if h.symbol == holding.symbol), None)
        if existing:
            # Update average price using weighted average
            total_shares = existing.shares + holding.shares
            total_value = (existing.shares * existing.avg_buy_price + 
                          holding.shares * holding.avg_buy_price)
            existing.avg_buy_price = total_value / total_shares if total_shares > 0 else 0
            existing.shares = total_shares
        else:
            self.holdings.append(holding)
        self.updated_at = datetime.now().isoformat()
    
    def remove_holding(self, symbol: str, shares: Optional[float] = None):
        """Remove holding entirely or reduce shares."""
        holding = next((h for h in self.holdings if h.symbol == symbol), None)
        if not holding:
            raise ValueError(f"Symbol {symbol} not found in portfolio")
        
        if shares is None or shares >= holding.shares:
            # Remove completely
            self.holdings.remove(holding)
        else:
            # Reduce shares
            holding.shares -= shares
        
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "holdings": [h.to_dict() for h in self.holdings],
            "cash_balance": self.cash_balance,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Portfolio':
        """Create Portfolio from dictionary."""
        holdings = [Holding.from_dict(h) for h in data.get("holdings", [])]
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            holdings=holdings,
            cash_balance=data.get("cash_balance", 0.0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
    
    def save(self, directory: Path):
        """Save portfolio to JSON file."""
        directory.mkdir(parents=True, exist_ok=True)
        filepath = directory / f"portfolio_{self.user_id}.json"
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, user_id: str, directory: Path) -> Optional['Portfolio']:
        """Load portfolio from JSON file."""
        filepath = directory / f"portfolio_{user_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
