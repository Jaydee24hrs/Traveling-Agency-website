from datetime import datetime, timedelta


def split_payments_with_dates(payment_case, amount, start_date):
    # Define a dictionary to map payment cases to their corresponding values
    payment_mapping = {
        'nextday': {'percentage': 0.50, 'total_percentage': 0.05, 'end_interval_days': 1},
        'oneweek': {'percentage': 0.50, 'total_percentage': 0.10, 'end_interval_days': 7},
        'twoweek': {'percentage': 0.40, 'total_percentage': 0.15, 'end_interval_days': 14},
        'threeweek': {'percentage': 0.40, 'total_percentage': 0.20, 'end_interval_days': 21},
        'onemonths': {'percentage': 0.40, 'total_percentage': 0.25, 'end_interval_days': 30},
        'twomonths': {'percentage': 0.40, 'total_percentage': 0.30, 'end_interval_days': 60},
    }

    # Get the details based on the payment case
    payment_details = payment_mapping.get(payment_case)

    if payment_details:
        # Adjust the amount to include the total percentage
        amount += amount * payment_details['total_percentage']

        # Define initial payment details
        first_payment_percentage = payment_details['percentage']
        first_payment = amount * first_payment_percentage
        remaining_amount = amount - first_payment

        # Calculate the amounts for up to 3 payments
        remaining_payment = remaining_amount / 2 if remaining_amount > 0 else 0

        # Calculate interval based on end interval and number of payments (3 max)
        end_interval_days = payment_details['end_interval_days']
        interval_days = end_interval_days // 2  # Three payments spread across the total interval

        # Create a list to store payment amounts and their due dates
        payment_schedule = [
            {'amount': first_payment, 'due_date': start_date}  # First payment is due on the start date
        ]

        # Calculate due dates for each additional payment
        for i in range(1, 3):  # Limit to a max of 3 payments
            due_date = start_date + timedelta(days=interval_days * i)
            payment_schedule.append({
                'amount': remaining_payment,
                'due_date': due_date
            })

        return payment_schedule
    else:
        raise ValueError("Invalid payment case provided.")


# Example usage
try:
    payment_case = 'twomonths'  # Change this to test different cases
    amount = 245200  # The base amount for calculation
    start_date = datetime.now()  # Starting date for the payment schedule
    payment_schedule = split_payments_with_dates(payment_case, amount, start_date)

    for payment in payment_schedule:
        print(f"Payment Amount: {payment['amount']}, Due Date: {payment['due_date'].strftime('%Y-%m-%d')}")
except ValueError as e:
    print(e)
