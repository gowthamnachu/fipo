from django.db import models

class Investment(models.Model):
    CATEGORY_CHOICES = [
        ('Equity', 'Equity'),
        ('Mutual Funds', 'Mutual Funds'),
        ('Bonds', 'Bonds'),
        ('Gold', 'Gold'),
        ('Real Estate', 'Real Estate'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    percentage = models.FloatField()
    amount = models.FloatField()

    def __str__(self):
        return f"{self.category}: {self.amount} INR"
from django.db import models

class TaxOptimization(models.Model):
    annual_income = models.FloatField()
    suggested_strategy = models.TextField()

    def __str__(self):
        return f"Tax Optimization for Income: {self.annual_income}"
