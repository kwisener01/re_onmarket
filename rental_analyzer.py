"""
FYNIX Rental Analyzer - Analyze rental investment potential
Calculate cash flow, ROI, cap rate, and rental property metrics
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import http.client
import json
import os
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class RentalAnalyzer:
    """Analyze rental property investment potential"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ZILLOW_API_KEY')
        self.api_host = "zillow-working-api.p.rapidapi.com"

        if not self.api_key:
            raise ValueError("API key not found. Set ZILLOW_API_KEY in .env file")

    def get_rent_history(self, zpid: str = None, url: str = None, address: str = None) -> Optional[Dict]:
        """
        Get rent estimate history for a property

        Args:
            zpid: Zillow Property ID
            url: Zillow property URL
            address: Property address

        Returns:
            Rent estimate history data
        """
        if not any([zpid, url, address]):
            raise ValueError("Must provide zpid, url, or address")

        # Build query parameters
        params = ["recent_first=True", "which=rent_zestimate_history"]

        if zpid:
            params.append(f"byzpid={zpid}")
        if url:
            encoded_url = url.replace(":", "%3A").replace("/", "%2F")
            params.append(f"byurl={encoded_url}")
        if address:
            encoded_addr = address.replace(" ", "%20").replace(",", "%2C")
            params.append(f"byaddress={encoded_addr}")

        endpoint = f"/graph_charts?{'&'.join(params)}"

        print(f"\n💰 Fetching rent estimate data...")
        if zpid:
            print(f"🆔 ZPID: {zpid}")
        if address:
            print(f"📍 Address: {address}")
        print()

        try:
            conn = http.client.HTTPSConnection(self.api_host)

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }

            conn.request("GET", endpoint, headers=headers)

            res = conn.getresponse()
            data = res.read()

            print(f"✅ API Response Status: {res.status}\n")

            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                print(f"❌ API Error: {res.status}")
                print(f"Response: {data.decode('utf-8')}\n")
                return None

        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return None
        finally:
            conn.close()

    def analyze_rental_investment(
        self,
        purchase_price: float,
        monthly_rent: float,
        down_payment_pct: float = 20,
        interest_rate: float = 7.0,
        loan_term_years: int = 30,
        closing_costs_pct: float = 3,
        property_tax_pct: float = 1.2,
        insurance_monthly: float = 150,
        hoa_monthly: float = 0,
        maintenance_pct: float = 1.0,
        vacancy_rate_pct: float = 5,
        property_mgmt_pct: float = 10
    ) -> Dict:
        """
        Comprehensive rental investment analysis

        Returns:
            Detailed rental metrics including cash flow, ROI, cap rate
        """
        # Initial investment
        down_payment = purchase_price * (down_payment_pct / 100)
        loan_amount = purchase_price - down_payment
        closing_costs = purchase_price * (closing_costs_pct / 100)
        total_initial_investment = down_payment + closing_costs

        # Monthly mortgage payment (P&I)
        monthly_rate = (interest_rate / 100) / 12
        num_payments = loan_term_years * 12

        if monthly_rate > 0:
            monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                             ((1 + monthly_rate)**num_payments - 1)
        else:
            monthly_mortgage = loan_amount / num_payments

        # Monthly expenses
        property_tax_monthly = (purchase_price * (property_tax_pct / 100)) / 12
        maintenance_monthly = (purchase_price * (maintenance_pct / 100)) / 12
        property_mgmt_monthly = monthly_rent * (property_mgmt_pct / 100)

        total_monthly_expenses = (
            monthly_mortgage +
            property_tax_monthly +
            insurance_monthly +
            hoa_monthly +
            maintenance_monthly +
            property_mgmt_monthly
        )

        # Income calculations
        vacancy_loss = monthly_rent * (vacancy_rate_pct / 100)
        effective_monthly_income = monthly_rent - vacancy_loss

        # Cash flow
        monthly_cash_flow = effective_monthly_income - total_monthly_expenses
        annual_cash_flow = monthly_cash_flow * 12

        # ROI metrics
        cash_on_cash_return = (annual_cash_flow / total_initial_investment * 100) if total_initial_investment > 0 else 0

        # Cap rate (annual NOI / purchase price)
        annual_noi = (effective_monthly_income * 12) - (
            (property_tax_monthly + insurance_monthly + hoa_monthly + maintenance_monthly + property_mgmt_monthly) * 12
        )
        cap_rate = (annual_noi / purchase_price * 100) if purchase_price > 0 else 0

        # Break-even analysis
        break_even_rent = total_monthly_expenses / (1 - (vacancy_rate_pct / 100))
        rent_to_price_ratio = (monthly_rent * 12) / purchase_price if purchase_price > 0 else 0

        # 1% Rule check
        one_percent_rule = monthly_rent >= (purchase_price * 0.01)

        # Investment grade
        if cash_on_cash_return >= 12 and cap_rate >= 8:
            grade = "A+ EXCELLENT"
            verdict = "🔥 STRONG BUY - Exceptional rental investment"
        elif cash_on_cash_return >= 8 and cap_rate >= 6:
            grade = "A VERY GOOD"
            verdict = "✅ BUY - Great rental opportunity"
        elif cash_on_cash_return >= 5 and cap_rate >= 4:
            grade = "B GOOD"
            verdict = "💰 BUY - Solid rental investment"
        elif cash_on_cash_return >= 0:
            grade = "C FAIR"
            verdict = "⚠️ CONDITIONAL - Marginal cash flow"
        else:
            grade = "D POOR"
            verdict = "❌ PASS - Negative cash flow"

        return {
            "purchase_analysis": {
                "purchase_price": purchase_price,
                "down_payment": down_payment,
                "loan_amount": loan_amount,
                "closing_costs": closing_costs,
                "total_initial_investment": total_initial_investment
            },
            "income": {
                "monthly_rent": monthly_rent,
                "annual_rent": monthly_rent * 12,
                "vacancy_loss_monthly": vacancy_loss,
                "effective_monthly_income": effective_monthly_income,
                "effective_annual_income": effective_monthly_income * 12
            },
            "expenses": {
                "monthly_mortgage": monthly_mortgage,
                "property_tax_monthly": property_tax_monthly,
                "insurance_monthly": insurance_monthly,
                "hoa_monthly": hoa_monthly,
                "maintenance_monthly": maintenance_monthly,
                "property_mgmt_monthly": property_mgmt_monthly,
                "total_monthly_expenses": total_monthly_expenses,
                "total_annual_expenses": total_monthly_expenses * 12
            },
            "cash_flow": {
                "monthly_cash_flow": monthly_cash_flow,
                "annual_cash_flow": annual_cash_flow
            },
            "roi_metrics": {
                "cash_on_cash_return": round(cash_on_cash_return, 2),
                "cap_rate": round(cap_rate, 2),
                "annual_noi": annual_noi,
                "rent_to_price_ratio": round(rent_to_price_ratio, 4)
            },
            "benchmarks": {
                "one_percent_rule_met": one_percent_rule,
                "one_percent_target": purchase_price * 0.01,
                "break_even_rent": break_even_rent
            },
            "rating": {
                "grade": grade,
                "verdict": verdict
            },
            "assumptions": {
                "down_payment_pct": down_payment_pct,
                "interest_rate": interest_rate,
                "loan_term_years": loan_term_years,
                "vacancy_rate_pct": vacancy_rate_pct,
                "property_mgmt_pct": property_mgmt_pct
            }
        }


def format_currency(amount):
    """Format number as currency"""
    return f"${amount:,.2f}"


def print_rental_analysis(analysis: Dict):
    """Pretty print rental analysis"""

    print("\n" + "="*80)
    print("🏠 FYNIX RENTAL INVESTMENT ANALYSIS")
    print("="*80 + "\n")

    # Purchase Summary
    pa = analysis['purchase_analysis']
    print("💵 PURCHASE SUMMARY")
    print("-"*80)
    print(f"Purchase Price:        {format_currency(pa['purchase_price'])}")
    print(f"Down Payment (20%):    {format_currency(pa['down_payment'])}")
    print(f"Loan Amount:           {format_currency(pa['loan_amount'])}")
    print(f"Closing Costs (3%):    {format_currency(pa['closing_costs'])}")
    print(f"Total Cash Needed:     {format_currency(pa['total_initial_investment'])}")

    # Income
    inc = analysis['income']
    print("\n" + "-"*80)
    print("💰 RENTAL INCOME")
    print("-"*80)
    print(f"Monthly Rent:          {format_currency(inc['monthly_rent'])}")
    print(f"Annual Rent:           {format_currency(inc['annual_rent'])}")
    print(f"Vacancy Loss (5%):     -{format_currency(inc['vacancy_loss_monthly'])}/mo")
    print(f"Effective Income:      {format_currency(inc['effective_monthly_income'])}/mo")

    # Expenses
    exp = analysis['expenses']
    print("\n" + "-"*80)
    print("📊 MONTHLY EXPENSES")
    print("-"*80)
    print(f"Mortgage (P&I):        {format_currency(exp['monthly_mortgage'])}")
    print(f"Property Tax:          {format_currency(exp['property_tax_monthly'])}")
    print(f"Insurance:             {format_currency(exp['insurance_monthly'])}")
    print(f"HOA:                   {format_currency(exp['hoa_monthly'])}")
    print(f"Maintenance (1%):      {format_currency(exp['maintenance_monthly'])}")
    print(f"Property Mgmt (10%):   {format_currency(exp['property_mgmt_monthly'])}")
    print(f"{'─'*80}")
    print(f"Total Expenses:        {format_currency(exp['total_monthly_expenses'])}")

    # Cash Flow
    cf = analysis['cash_flow']
    print("\n" + "-"*80)
    print("💵 CASH FLOW")
    print("-"*80)
    monthly_color = "✅" if cf['monthly_cash_flow'] >= 0 else "❌"
    print(f"Monthly Cash Flow:     {monthly_color} {format_currency(cf['monthly_cash_flow'])}")
    print(f"Annual Cash Flow:      {format_currency(cf['annual_cash_flow'])}")

    # ROI Metrics
    roi = analysis['roi_metrics']
    print("\n" + "-"*80)
    print("📈 ROI METRICS")
    print("-"*80)
    print(f"Cash-on-Cash Return:   {roi['cash_on_cash_return']:.2f}%")
    print(f"Cap Rate:              {roi['cap_rate']:.2f}%")
    print(f"Annual NOI:            {format_currency(roi['annual_noi'])}")
    print(f"Rent-to-Price Ratio:   {roi['rent_to_price_ratio']:.2%}")

    # Benchmarks
    bench = analysis['benchmarks']
    print("\n" + "-"*80)
    print("🎯 INVESTMENT BENCHMARKS")
    print("-"*80)
    one_pct_status = "✅ PASS" if bench['one_percent_rule_met'] else "❌ FAIL"
    print(f"1% Rule:               {one_pct_status}")
    print(f"  Target Rent:         {format_currency(bench['one_percent_target'])}/mo")
    print(f"  Actual Rent:         {format_currency(inc['monthly_rent'])}/mo")
    print(f"Break-Even Rent:       {format_currency(bench['break_even_rent'])}/mo")

    # Rating
    rating = analysis['rating']
    print("\n" + "-"*80)
    print("⭐ INVESTMENT GRADE")
    print("-"*80)
    print(f"Grade: {rating['grade']}")
    print(f"{rating['verdict']}")

    # Recommendations
    print("\n" + "-"*80)
    print("💡 RECOMMENDATIONS")
    print("-"*80)

    if roi['cash_on_cash_return'] < 0:
        print("❌ Negative cash flow - This property will cost you money each month")
        print("   Consider: Higher rent, larger down payment, or different property")
    elif roi['cash_on_cash_return'] < 5:
        print("⚠️  Low returns - Consider if appreciation potential justifies investment")
    elif bench['one_percent_rule_met']:
        print("🔥 Meets 1% rule - Strong rental fundamentals")
        print("✅ Good cash flow metrics for rental investment")
    else:
        print("✅ Positive cash flow but below 1% rule")
        print("   Still viable if property is in appreciating market")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='FYNIX Rental Analyzer - Evaluate rental investment potential',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get rent estimate history
  python rental_analyzer.py --zpid 30907787 --history

  # Analyze rental investment
  python rental_analyzer.py --price 200000 --rent 1800

  # Full analysis with custom parameters
  python rental_analyzer.py --price 200000 --rent 1800 --down 25 --rate 6.5

  # Get rent estimate and analyze
  python rental_analyzer.py --zpid 14341709 --price 73500 --analyze
        """
    )

    parser.add_argument('--zpid', help='Zillow Property ID')
    parser.add_argument('--address', help='Property address')
    parser.add_argument('--url', help='Zillow property URL')

    parser.add_argument('--history', action='store_true', help='Show rent estimate history')
    parser.add_argument('--analyze', action='store_true', help='Perform rental investment analysis')

    parser.add_argument('--price', type=float, help='Purchase price')
    parser.add_argument('--rent', type=float, help='Monthly rent amount')

    parser.add_argument('--down', type=float, default=20, help='Down payment percentage (default: 20)')
    parser.add_argument('--rate', type=float, default=7.0, help='Interest rate (default: 7.0)')
    parser.add_argument('--term', type=int, default=30, help='Loan term in years (default: 30)')

    parser.add_argument('--save', help='Save results to JSON file', metavar='FILENAME')
    parser.add_argument('--raw', action='store_true', help='Show raw API response')

    args = parser.parse_args()

    analyzer = RentalAnalyzer()

    # Get rent history if requested
    if args.history or (any([args.zpid, args.url, args.address]) and not args.analyze):
        if not any([args.zpid, args.url, args.address]):
            parser.error("Must provide --zpid, --url, or --address for rent history")

        rent_data = analyzer.get_rent_history(
            zpid=args.zpid,
            url=args.url,
            address=args.address
        )

        if rent_data and args.raw:
            print("\n" + "="*80)
            print("RAW RENT ESTIMATE DATA")
            print("="*80 + "\n")
            print(json.dumps(rent_data, indent=2))

    # Perform rental analysis if requested
    if args.analyze or (args.price and args.rent):
        if not args.price or not args.rent:
            parser.error("Must provide --price and --rent for analysis")

        analysis = analyzer.analyze_rental_investment(
            purchase_price=args.price,
            monthly_rent=args.rent,
            down_payment_pct=args.down,
            interest_rate=args.rate,
            loan_term_years=args.term
        )

        print_rental_analysis(analysis)

        if args.save:
            with open(args.save, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"💾 Analysis saved to: {args.save}\n")
