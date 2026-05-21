"""
Supply Utility Functions for UTAS Simulation

Supply is now a monetary-based status with threshold mapping:
- Supply 1: $1 - $10,000
- Supply 2: $10,001 - $100,000  
- Supply 3: $100,001 - $1,000,000
- Supply 4: $1,000,001 - $10,000,000
- Supply 5: $10,000,001+
"""

def get_supply_status_from_money(money_amount: int) -> int:
    """
    Convert monetary amount to Supply status level (1-5)
    
    Args:
        money_amount: Amount of money in dollars
        
    Returns:
        Supply status level (1-5)
    """
    if money_amount <= 0:
        return 0
    elif money_amount <= 10_000:
        return 1
    elif money_amount <= 100_000:
        return 2
    elif money_amount <= 1_000_000:
        return 3
    elif money_amount <= 10_000_000:
        return 4
    else:
        return 5


def get_money_from_supply_status(supply_status: int) -> int:
    """
    Get the minimum monetary amount for a given Supply status level
    
    Args:
        supply_status: Supply status level (0-5)
        
    Returns:
        Minimum money amount for that status level
    """
    thresholds = {
        0: 0,
        1: 1,
        2: 10_001,
        3: 100_001,
        4: 1_000_001,
        5: 10_000_001
    }
    return thresholds.get(supply_status, 0)


def get_supply_status_range(supply_status: int) -> tuple[int, int]:
    """
    Get the monetary range for a given Supply status level
    
    Args:
        supply_status: Supply status level (0-5)
        
    Returns:
        Tuple of (min_amount, max_amount). Max is None for highest tier.
    """
    ranges = {
        0: (0, 0),
        1: (1, 10_000),
        2: (10_001, 100_000),
        3: (100_001, 1_000_000),
        4: (1_000_001, 10_000_000),
        5: (10_000_001, None)
    }
    return ranges.get(supply_status, (0, 0))


def format_money_display(money_amount: int) -> str:
    """
    Format money amount for display with appropriate suffixes
    
    Args:
        money_amount: Amount of money in dollars
        
    Returns:
        Formatted string (e.g., "$1.2M", "$500K", "$50")
    """
    if money_amount == 0:
        return "$0"
    elif money_amount < 1_000:
        return f"${money_amount:,}"
    elif money_amount < 1_000_000:
        return f"${money_amount / 1_000:.1f}K"
    elif money_amount < 1_000_000_000:
        return f"${money_amount / 1_000_000:.1f}M"
    else:
        return f"${money_amount / 1_000_000_000:.1f}B"


def get_supply_descriptor(supply_status: int) -> str:
    """
    Get descriptive text for Supply status level
    
    Args:
        supply_status: Supply status level (0-5)
        
    Returns:
        Descriptive string for the wealth level
    """
    descriptors = {
        0: "Bankrupt",
        1: "Poor",
        2: "Lower Middle Class",
        3: "Upper Middle Class", 
        4: "Wealthy",
        5: "Ultra Wealthy"
    }
    return descriptors.get(supply_status, "Unknown")


def calculate_supply_shift_from_money_change(current_money: int, money_change: int) -> tuple[int, int, int]:
    """
    Calculate how a monetary change affects Supply status
    
    Args:
        current_money: Current monetary amount
        money_change: Change in money (positive or negative)
        
    Returns:
        Tuple of (old_status, new_money, new_status)
    """
    old_status = get_supply_status_from_money(current_money)
    new_money = max(0, current_money + money_change)
    new_status = get_supply_status_from_money(new_money)
    
    return old_status, new_money, new_status


def get_typical_money_for_status(supply_status: int) -> int:
    """
    Get a typical/default money amount for a given Supply status level
    Used for character creation and examples
    
    Args:
        supply_status: Supply status level (1-5)
        
    Returns:
        Typical money amount for that status level
    """
    typical_amounts = {
        0: 0,
        1: 5_000,
        2: 50_000,
        3: 500_000,
        4: 5_000_000,
        5: 50_000_000
    }
    return typical_amounts.get(supply_status, 0)
