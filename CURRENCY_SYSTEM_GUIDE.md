# 💰 CURRENCY SYSTEM - USER GUIDE

## ✅ **FULLY INTEGRATED & WORKING**

The currency system is completely integrated into the main simulation loop and processes all monetary transactions automatically.

---

## 🎯 **HOW IT WORKS**

### **1. Automatic Detection**
When you enter an action, the system automatically detects if it involves money:

**Examples of detected transactions:**
- "I buy a coffee for $5"
- "I order the breakfast special"
- "I give the waitress a $10 tip"
- "I sell my old watch"
- "I try to bribe the guard with $50"

### **2. Transaction Types**

The system recognizes these transaction types:

| Type | Description | Example |
|------|-------------|---------|
| **Purchase** | Buying items/services | "I buy coffee" |
| **Sale** | Selling items | "I sell my watch" |
| **Gift** | Giving money/items | "I tip the waitress $10" |
| **Bribe** | Attempting to influence | "I bribe the guard" |
| **Theft** | Stealing | "I pickpocket him" |
| **Gambling** | Betting/wagering | "I bet $20 on red" |
| **Service** | Paying for services | "I pay for repairs" |

### **3. Affordability Check**

**Before processing:**
- System checks if you have enough money
- If insufficient funds, transaction is blocked
- You'll see: "❌ Insufficient funds! You have $X but need $Y"

### **4. Item Creation**

**When you buy something:**
- Item is automatically added to your inventory
- You'll see: "📦 Added to inventory: [item name]"
- Items may have supplement bonuses

### **5. Money Transfer**

**Automatic money flow:**
- Your balance decreases (purchases, gifts, bribes)
- Vendor's balance increases
- You'll see updated balances after transaction

---

## 📋 **EXAMPLE TRANSACTIONS**

### **Example 1: Simple Purchase**
```
You: I order the breakfast special for $8.50

System detects:
- Transaction Type: Purchase
- Amount: -$8.50
- Item: Breakfast Special
- Creates Item: Yes

Result:
✅ Transaction approved
💰 Your balance: $100.00 → $91.50
💰 Vendor balance: $50.00 → $58.50
📦 Added to inventory: Breakfast Special
```

### **Example 2: Giving a Tip (Gift)**
```
You: I give the waitress a $5 tip

System detects:
- Transaction Type: Gift
- Amount: -$5.00
- Item: tip
- Creates Item: No

Result:
✅ Transaction approved
💰 Your balance: $91.50 → $86.50
💰 Waitress balance: $58.50 → $63.50
💝 Sympathy shift: +1 (they appreciate the gesture)
```

### **Example 3: Insufficient Funds**
```
You: I buy the expensive watch for $200

System detects:
- Transaction Type: Purchase
- Amount: -$200.00
- Your balance: $86.50

Result:
❌ Insufficient funds!
You have $86.50 but the expensive watch costs $200.00
(Transaction blocked, no changes made)
```

### **Example 4: Selling an Item**
```
You: I sell my old jacket to the vendor

System detects:
- Transaction Type: Sale
- Amount: +$15.00 (estimated)
- Removes Item: Old Jacket

Result:
✅ Transaction approved
💰 Your balance: $86.50 → $101.50
💰 Vendor balance: $63.50 → $48.50
📦 Removed from inventory: Old Jacket
```

### **Example 5: Bribe (Success)**
```
You: I bribe the guard with $50

System detects:
- Transaction Type: Bribe
- Amount: -$50.00

UTAS Resolution:
- Your attempt: 8 successes
- Guard's resistance: 3 successes
- Result: You win

Result:
✅ Bribe successful
💰 Your balance: $101.50 → $51.50
💰 Guard balance: $100.00 → $150.00
💝 Sympathy shift: +2 (guard is now friendly)
```

### **Example 6: Bribe (Failure)**
```
You: I bribe the official with $30

System detects:
- Transaction Type: Bribe
- Amount: -$30.00

UTAS Resolution:
- Your attempt: 2 successes
- Official's resistance: 7 successes
- Result: Official wins

Result:
❌ Bribe rejected
💰 Your balance: $51.50 → $21.50 (money still taken!)
💰 Official balance: $200.00 → $230.00
💔 Sympathy shift: -2 (official is now hostile)
```

---

## 🔍 **CHECKING YOUR MONEY**

### **View Your Balance:**
Type `ua` or `sheet` to see your character sheet, which includes:
- Current money amount
- All inventory items
- Status levels

### **Money is Stored in SUPPLY Status:**
- Your money is tracked in the SUPPLY status
- Format: `SUPPLY: [level] ($[amount])`
- Example: `SUPPLY: Average (3) ($86.50)`

---

## 🎮 **INTEGRATION POINTS**

The currency system is integrated at these points:

### **1. ROAM Mode**
- **Detection:** Line 1914 in redesigned_main.py
- **Processing:** Lines 2304-2316 (given actions)
- **Affordability Check:** Lines 1919-1928

### **2. Encounter Mode (FAST Path)**
- **Detection:** Line 3607
- **Processing:** Lines 3258-3277
- **Affordability Check:** Lines 3613-3622

### **3. Encounter Mode (Standard Path)**
- **Detection:** Inherited from proactor action
- **Processing:** Lines 4188-4201

---

## 💡 **TIPS**

1. **Be Specific:** "I buy coffee for $5" works better than "I buy coffee"
2. **Check Balance:** Use `ua` command to see your money before big purchases
3. **Items Matter:** Purchased items go to inventory and can be used as supplements
4. **Bribes are Risky:** Failed bribes still cost money AND damage relationships
5. **Gifts Build Rapport:** Tipping/gifting increases sympathy with NPCs

---

## 🐛 **TROUBLESHOOTING**

**Transaction not detected?**
- Make sure to mention money explicitly ("$5", "5 dollars", "five bucks")
- Or mention the transaction type ("buy", "purchase", "pay for")

**Item not in inventory?**
- Check if `creates_item` was True in the detection
- Some transactions (tips, bribes) don't create items

**Wrong amount charged?**
- System estimates prices if not specified
- Be explicit: "I buy coffee for $5" vs "I buy coffee"

---

## ✅ **SYSTEM STATUS**

- ✅ Detection: Working
- ✅ Affordability checks: Working
- ✅ Money transfer: Working
- ✅ Item creation: Working
- ✅ Sympathy effects: Working
- ✅ Transaction narratives: Working

**The currency system is fully operational and ready to use!** 💰✨
