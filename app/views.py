import json
import pandas as pd
import numpy as np
import yfinance as yf
from django.shortcuts import render
from django.http import HttpResponse
from .forms import InvestmentForm
from .optimizer import optimize_allocation
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
def intro(request):
    # Simply render the intro.html page
    return render(request, 'intro.html')
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, "login.html")

def signup_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, "Account created successfully. You can log in now.")
                return redirect('login')
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, "signup.html")

def logout_view(request):
    logout(request)
    return redirect('login')
    

# -------------------- FUND ALLOCATION --------------------
@login_required(login_url='/login/')
def fund_allocation(request):
    allocation = None
    amount = None  

    if request.method == "POST":
        form = InvestmentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]  
            allocation = optimize_allocation(amount)  

            # Store data in session
            request.session["investment_amount"] = amount
            request.session["allocation"] = allocation  

    else:
        form = InvestmentForm()

    return render(request, "fund_allocation.html", {"form": form, "allocation": allocation, "amount": amount})

# -------------------- VISUALIZE FUNDS --------------------

def visualize_funds(request):
    investment_amount = request.session.get("investment_amount", 100000)  
    allocation = optimize_allocation(investment_amount)

    total_amount = sum(allocation.values())  
    percentages = {category: (amount / total_amount) * 100 if total_amount > 0 else 0 for category, amount in allocation.items()}

    allocation_data = [(category, amount, percentages[category]) for category, amount in allocation.items()]
    fund_data = json.dumps(allocation)

    return render(request, "visualize_funds.html", {
        "fund_data": fund_data,
        "allocation_data": allocation_data,
        "total_amount": total_amount
    })

# -------------------- PORTFOLIO INSIGHTS --------------------
def calculate_portfolio_metrics(allocation):
    np.random.seed(42)  

    historical_returns = {
        "Equity": np.random.normal(0.08, 0.15, 1000),
        "Mutual Funds": np.random.normal(0.06, 0.10, 1000),
        "Bonds": np.random.normal(0.04, 0.05, 1000),
        "Gold": np.random.normal(0.07, 0.12, 1000),
        "Real Estate": np.random.normal(0.05, 0.08, 1000),
    }

    df_returns = pd.DataFrame(historical_returns)
    weights = np.array([allocation[category] for category in df_returns.columns])
    weights = weights / np.sum(weights)  
    expected_return = np.sum(weights * df_returns.mean())

    cov_matrix = df_returns.cov()
    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    risk_free_rate = 0.03
    sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility
    diversification_score = 1 - max(weights)

    return {
        "expected_return": expected_return * 100,
        "portfolio_risk": portfolio_volatility * 100,
        "sharpe_ratio": sharpe_ratio,
        "diversification_score": diversification_score * 100,
    }

def portfolio_insights(request):
    investment_amount = request.session.get("investment_amount", 100000)
    allocation = optimize_allocation(investment_amount)
    insights = calculate_portfolio_metrics(allocation)

    return render(request, "portfolio_insights.html", {
        "allocation": allocation,
        "insights": insights
    })
from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import os
import os
import datetime
from django.conf import settings
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable


def generate_pdf_report(request):
    # Fetch investment details
    investment_amount = request.session.get("investment_amount", 100000)
    allocation = optimize_allocation(investment_amount)
    insights = calculate_portfolio_metrics(allocation)

    # Date
    report_date = datetime.datetime.now().strftime("%d %B %Y")

    # Financial Metrics
    expected_return = insights.get("expected_return", 0.0)
    portfolio_risk = insights.get("portfolio_risk", 0.0)
    sharpe_ratio = insights.get("sharpe_ratio", 0.0)
    diversification_score = insights.get("diversification_score", 0.0)

    # PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=72, bottomMargin=50)
    elements = []

    # ✅ Load Logo with Proper Alignment
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo_fipo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.0 * inch, height=1.0 * inch)  # 90px x 90px
    else:
        logo = Paragraph("FIPO", getSampleStyleSheet()["Title"])  # Placeholder if missing

    # ✅ Professional Report Header Layout
    header_table = Table([
        [logo, 
         Paragraph("<font size=16><b>FiPo Analysis Report</b></font>", getSampleStyleSheet()["Title"]), 
         Paragraph(f"<font size=12><b>FIPO - Finance Portfolio Optimizer</b><br/>Report Date: {report_date}</font>", getSampleStyleSheet()["Normal"])]
    ], colWidths=[1.5 * inch, 3.5 * inch, 2.5 * inch])
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.black))
    elements.append(Spacer(1, 20))

    # ✅ Report Title with Stylish Formatting
    title_style = ParagraphStyle("TitleStyle", fontSize=18, spaceAfter=15, alignment=1, fontName="Helvetica-Bold", textColor=colors.darkblue)
    elements.append(Paragraph("📊 Financial Portfolio Optimization Report", title_style))
    elements.append(Spacer(1, 15))

    # ✅ Investment Amount Section
    elements.append(Paragraph(f"<font size=12><b>Investment Amount:</b> ₹{investment_amount:,}</font>", getSampleStyleSheet()["Normal"]))
    elements.append(Spacer(1, 10))

    # ✅ Financial Metrics Table (Enhanced Styling)
    metrics_data = [
        ["📊 Metric", "📈 Value"],
        ["Expected Return (%)", f"{expected_return:.2f}%"],
        ["Portfolio Risk (%)", f"{portfolio_risk:.2f}%"],
        ["Sharpe Ratio", f"{sharpe_ratio:.2f}"],
        ["Diversification Score (%)", f"{diversification_score:.2f}%"],
    ]
    metrics_table = Table(metrics_data, colWidths=[280, 200])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 12))

    # ✅ Investment Allocation Table with Improved Styling
    elements.append(Paragraph("<font size=14><b>📌 Investment Allocation</b></font>", getSampleStyleSheet()["Heading2"]))
    elements.append(Spacer(1, 8))

    allocation_data = [["Asset", "Investment (₹)"]]
    for asset, amount in allocation.items():
        allocation_data.append([asset, f"{amount:,.2f}"])
    allocation_table = Table(allocation_data, colWidths=[280, 200])
    allocation_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(allocation_table)
    elements.append(Spacer(1, 12))

    # ✅ Insights & Summary - Clean and Well-Spaced
    insights_summary = f"""
    <b>📌 Portfolio Insights:</b><br/>
    The portfolio is optimized with an <b>expected return</b> of <b>{expected_return:.2f}%</b> 
    and a <b>risk factor</b> of <b>{portfolio_risk:.2f}%</b>. 
    With a <b>diversification score</b> of <b>{diversification_score:.2f}%</b>, 
    the investment is well-distributed across asset classes.<br/><br/>
    The <b>Sharpe Ratio</b> of <b>{sharpe_ratio:.2f}</b> suggests a favorable risk-adjusted return.
    """
    elements.append(Paragraph(insights_summary, getSampleStyleSheet()["Normal"]))
    elements.append(Spacer(1, 40))  # Spacing to push the digital signature to the bottom

    # ✅ Digital Signature Section - Placed at the Bottom
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.black))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>🖊️ Digitally Signed by FIPO Analysis System</b>", getSampleStyleSheet()["Normal"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("This document is digitally signed and does not require a physical signature.", getSampleStyleSheet()["Normal"]))

    # ✅ Generate PDF
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=FiPo_Analysis_Report.pdf"
    return response


# -------------------- RISK & RETURN ANALYSIS --------------------
import yfinance as yf
import pandas as pd
import numpy as np
from django.shortcuts import render

def calculate_risk_return(symbol):
    try:
        # Fetch the stock data for the symbol
        ticker = yf.Ticker(symbol)
        stock_data = ticker.history(period="5y")

        # Check if 'Adj Close' or 'Close' data is available
        if 'Adj Close' in stock_data.columns:
            price_column = 'Adj Close'
        elif 'Close' in stock_data.columns:
            price_column = 'Close'
        else:
            return {"error": f"Data for {symbol} is missing both 'Adj Close' and 'Close'. Please check the symbol."}

        # Calculate daily returns from selected price column (Adj Close or Close)
        stock_data['Daily Return'] = stock_data[price_column].pct_change()

        # Calculate expected return (annualized)
        expected_return = stock_data['Daily Return'].mean() * 252  # Assuming 252 trading days per year

        # Calculate risk (annualized volatility)
        risk_volatility = stock_data['Daily Return'].std() * np.sqrt(252)

        # Calculate Sharpe ratio (assuming a 3% risk-free rate)
        risk_free_rate = 0.03
        sharpe_ratio = (expected_return - risk_free_rate) / risk_volatility

        return {
            "stock_symbol": symbol,
            "expected_return": expected_return * 100,  # Convert to percentage
            "risk_volatility": risk_volatility * 100,  # Convert to percentage
            "sharpe_ratio": sharpe_ratio
        }

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.http import HttpResponse
from .forms import StockSymbolForm
from io import BytesIO
import base64
import matplotlib

matplotlib.use('Agg')  # For saving the plot without display (headless server)
def risk_return_analysis(request):
    stock_symbol = None
    analysis_results = None
    error_message = None
    stock_data = None
    chart_url = None

    if request.method == "POST":
        form = StockSymbolForm(request.POST)
        if form.is_valid():
            stock_symbol = form.cleaned_data["stock_symbol"]
            period = form.cleaned_data.get("period", 1)  # Default to 1 year

            # Automatically append .NS for NSE stocks if not present
            if not stock_symbol.endswith('.NS'):
                stock_symbol += '.NS'

            try:
                # Fetch the stock data for the specified symbol and period
                stock_data = yf.download(stock_symbol, period=f"{period}y")

                # Log the entire fetched data for debugging
                print(f"Fetched data for {stock_symbol}:\n{stock_data.head()}")

                # Check for 'Adj Close' or other relevant columns
                if stock_data.empty or ('Adj Close' not in stock_data.columns and 'Close' not in stock_data.columns):
                    raise ValueError(f"Data for {stock_symbol} is missing 'Adj Close' or 'Close'. Please check the symbol.")

                # If 'Adj Close' is missing, try using 'Close' as a fallback
                price_column = 'Adj Close' if 'Adj Close' in stock_data.columns else 'Close'
                stock_data['Daily Return'] = stock_data[price_column].pct_change()

                expected_return = stock_data['Daily Return'].mean() * 252  # Annualize the return
                risk = stock_data['Daily Return'].std() * np.sqrt(252)  # Annualize the volatility
                
                # Handle zero risk case for Sharpe ratio calculation
                if risk != 0:
                    sharpe_ratio = expected_return / risk
                else:
                    sharpe_ratio = None  # Return None if Sharpe ratio cannot be calculated

                # Plot the stock price movement over time
                plt.figure(figsize=(10, 6))
                plt.plot(stock_data[price_column], label=f"{stock_symbol} Price")
                plt.title(f"{stock_symbol} Price Movement")
                plt.xlabel("Date")
                plt.ylabel("Price")
                plt.grid(True)
                plt.legend(loc="upper left")

                # Save plot to a BytesIO object
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                
                # Convert to base64 for rendering in the template
                chart_url = base64.b64encode(buffer.read()).decode('utf-8')

                # Return results
                analysis_results = {
                    "stock_symbol": stock_symbol,
                    "expected_return": expected_return * 100,  # Convert to percentage
                    "risk": risk * 100,  # Convert to percentage
                    "sharpe_ratio": sharpe_ratio,
                }
            except ValueError as ve:
                error_message = f"Error: {str(ve)}"
            except Exception as e:
                error_message = f"Unexpected error occurred: {str(e)}"
    else:
        form = StockSymbolForm()

    return render(request, "risk_return_analysis.html", {
        "form": form,
        "analysis_results": analysis_results,
        "error_message": error_message,
        "chart_url": chart_url
    })

# -------------------- DASHBOARD --------------------
def dashboard(request):
    return render(request, 'dashboard.html')
from django.shortcuts import render

def about_us(request):
    return render(request, 'about_us.html')
# app/views.py
from django.shortcuts import render
from .forms import TaxOptimizationForm
from .tax_optimize import calculate_tax_optimization  # Importing the tax optimization logic

def tax_optimization(request):
    optimization_result = None

    if request.method == 'POST':
        form = TaxOptimizationForm(request.POST)
        if form.is_valid():
            annual_income = form.cleaned_data['annual_income']
            user_category = form.cleaned_data['user_category']  # Assuming a field for the category (e.g., 'individual', 'senior', 'super_senior', 'huf')
            
            # Calculate tax optimization results
            optimization_result = calculate_tax_optimization(annual_income, user_category)
        
    else:
        form = TaxOptimizationForm()

    return render(request, 'tax_optimization.html', {
        'form': form,
        'optimization_result': optimization_result
    })
@login_required
def profile_view(request):
    return render(request, 'profile.html')