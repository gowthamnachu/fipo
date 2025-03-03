from django import forms

class InvestmentForm(forms.Form):
    amount = forms.FloatField(label="Investment Amount (INR)")
from django import forms

class StockSymbolForm(forms.Form):
    stock_symbol = forms.CharField(max_length=10, label="Enter Stock Symbol")
    period = forms.ChoiceField(choices=[(1, "1 Year"), (3, "3 Years"), (5, "5 Years")], initial=1, label="Time Period")
from django import forms

class TaxOptimizationForm(forms.Form):
    annual_income = forms.DecimalField(label='Annual Income (INR)', max_digits=15, decimal_places=2)
    user_category = forms.ChoiceField(
        label='User Category',
        choices=[
            ('individual', 'Individual'),
            ('senior_citizen', 'Senior Citizen (60-80 years)'),
            ('super_senior_citizen', 'Super Senior Citizen (80+ years)'),
            ('huf', 'Hindu Undivided Family (HUF)')
        ],
        widget=forms.Select
    )
