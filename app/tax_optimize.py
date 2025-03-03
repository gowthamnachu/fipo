from decimal import Decimal, ROUND_HALF_UP

# Define tax brackets for different categories
TAX_BRACKETS = {
    'individual': [(250000, Decimal('0.05')), (500000, Decimal('0.20')), (1000000, Decimal('0.30'))],  # for regular individuals
    'senior_citizen': [(300000, Decimal('0.05')), (500000, Decimal('0.20')), (1000000, Decimal('0.30'))],  # for senior citizens (60-80)
    'super_senior_citizen': [(500000, Decimal('0.20')), (1000000, Decimal('0.30'))],  # for super senior citizens (80+)
    'huf': [(250000, Decimal('0.05')), (500000, Decimal('0.20')), (1000000, Decimal('0.30'))]  # for HUF
}

# Define surcharge ranges
SURCHARGE_RANGES = [
    (Decimal('5000000'), Decimal('0.37')),  # Above 5 Crore
    (Decimal('2000000'), Decimal('0.25')),  # 2 Crore to 5 Crore
    (Decimal('1000000'), Decimal('0.15')),  # 1 Crore to 2 Crore
    (Decimal('500000'), Decimal('0.10'))    # 50 Lakhs to 1 Crore
]

def calculate_tax_optimization(annual_income, user_category):
    """
    Function to calculate tax optimization based on annual income and user category.
    """
    # Convert income to Decimal for precise calculations
    annual_income = Decimal(annual_income)
    
    # Get the tax bracket for the user category
    tax_brackets = TAX_BRACKETS.get(user_category, TAX_BRACKETS['individual'])  # Default to individual if category not found
    tax = Decimal(0)
    remaining_income = annual_income

    # Apply tax based on brackets
    for bracket in tax_brackets:
        if remaining_income > bracket[0]:
            tax += (remaining_income - bracket[0]) * bracket[1]  # Now using Decimal percentages
            remaining_income = bracket[0]  # Update remaining income after applying this tax rate

    # Apply surcharge if applicable
    surcharge = apply_surcharge(annual_income)
    
    # Total tax including surcharge
    total_tax = tax + surcharge
    
    # Round the results to 2 decimal places
    total_tax = total_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    surcharge = surcharge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Calculate the suggested tax-saving strategy and profit gain
    suggested_strategy = get_tax_strategy(user_category)
    profit_gain = calculate_profit_gain(total_tax, annual_income)
    
    # Round the profit gain to 2 decimal places
    profit_gain = profit_gain.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Return the result as a dictionary
    return {
        'annual_income': annual_income,
        'total_tax': total_tax,
        'surcharge': surcharge,
        'suggested_strategy': suggested_strategy,
        'profit_gain': profit_gain
    }

def apply_surcharge(annual_income):
    """
    Function to calculate the surcharge based on the total income.
    """
    surcharge = Decimal(0)
    for limit, percentage in SURCHARGE_RANGES:
        if annual_income > limit:
            surcharge = (annual_income - limit) * percentage
            break
    return surcharge

def get_tax_strategy(user_category):
    """
    Function to provide a tax-saving strategy based on user category.
    """
    if user_category == 'individual':
        return "Invest in tax-efficient growth stocks, contribute to PPF, and utilize 80C deductions."
    elif user_category == 'senior_citizen':
        return "Focus on tax-saving FD schemes and senior citizen savings schemes (SCSS)."
    elif user_category == 'super_senior_citizen':
        return "Utilize senior citizen savings schemes (SCSS) and opt for tax-free bonds."
    elif user_category == 'huf':
        return "Optimize HUF tax savings through investment in tax-exempt bonds and equity funds."
    return "Consider optimizing your portfolio by utilizing tax-efficient strategies like PPF, NPS, and mutual funds."

def calculate_profit_gain(total_tax, annual_income):
    """
    Function to estimate the profit gain from tax-saving strategies.
    """
    total_tax = Decimal(total_tax)  # Ensure total_tax is a Decimal
    annual_income = Decimal(annual_income)  # Ensure annual_income is a Decimal

    # Refine profit gain calculation with dynamic thresholds
    profit_thresholds = {
        Decimal('0.05'): Decimal('0.10'),  # If tax is 5% or less, profit gain is 10% of income
        Decimal('0.10'): Decimal('0.15'),  # If tax is 10% or less, profit gain is 15% of income
        Decimal('0.20'): Decimal('0.20'),  # If tax is 20% or less, profit gain is 20% of income
    }
    
    for threshold, gain_percentage in profit_thresholds.items():
        if total_tax <= annual_income * threshold:
            return annual_income * gain_percentage
    
    # For very high tax values (high income), limit the profit gain
    return annual_income * Decimal('0.05')  # Set a fixed lower profit gain for large incomes
