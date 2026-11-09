import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

load_dotenv()
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def send_email(
    recipient_email, order_status, pickup_location, payment_method, items, total_price
):
    msg = EmailMessage()
    msg["From"] = formataddr(("Cookies4Cuties", SENDER_EMAIL))
    msg["To"] = recipient_email
    msg["Subject"] = f"🍪 Your cookies4cuties Order is {order_status.title()}!"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["Reply-To"] = SENDER_EMAIL

    # 1. Generate the HTML table rows for items dynamically
    item_rows_html = ""
    item_rows_text = []
    for item_name, item_details in items.items():
        item_rows_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eeeeee; font-family: sans-serif; font-size: 15px; color: #4a5568;">{item_name}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eeeeee; font-family: sans-serif; font-size: 15px; color: #4a5568; text-align: center;">{item_details[0]}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eeeeee; font-family: sans-serif; font-size: 15px; color: #4a5568; text-align: right;">₱{item_details[1]}</td>
        </tr>
        """
        item_rows_text.append(
            f"{item_name}: {item_details[0]} pcs | Total: {item_details[1]}"
        )

    # 2. Build the main HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f7fafc; -webkit-text-size-adjust: 100%;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f7fafc; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden;">
                        
                        <!-- Header Banner -->
                        <tr>
                            <td align="center" style="background-color: #fed7aa; padding: 30px 20px;">
                                <h1 style="margin: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 28px; color: #7c2d12; font-weight: bold; letter-spacing: -0.5px;">
                                    🍪 Cookies4Cuties
                                </h1>
                            </td>
                        </tr>

                        <!-- Body Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 16px 0; font-family: sans-serif; font-size: 22px; color: #1a202c;">Thank you for your order!</h2>
                                <p style="margin: 0 0 24px 0; font-family: sans-serif; font-size: 16px; line-height: 1.6; color: #4a5568;">
                                    We're baking your treats with love. Below is the summary of your order and the details for your upcoming pick-up.
                                </p>

                                <!-- Order Summary Table -->
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 30px; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background-color: #f8fafc;">
                                            <th align="left" style="padding: 12px; font-family: sans-serif; font-size: 14px; font-weight: bold; color: #64748b; border-bottom: 2px solid #e2e8f0;">Item</th>
                                            <th align="center" style="padding: 12px; font-family: sans-serif; font-size: 14px; font-weight: bold; color: #64748b; border-bottom: 2px solid #e2e8f0; width: 80px;">Qty</th>
                                            <th align="right" style="padding: 12px; font-family: sans-serif; font-size: 14px; font-weight: bold; color: #64748b; border-bottom: 2px solid #e2e8f0; width: 80px;">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {item_rows_html}
                                    </tbody>
                                </table>

                                <!-- Order Metadata Grid -->
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #fff7ed; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                                    <tr>
                                        <td style="padding-bottom: 10px; font-family: sans-serif; font-size: 14px; color: #7c2d12;">
                                            <strong>Order Status:</strong> <span style="text-transform: capitalize; background-color: #ffedd5; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{order_status}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-bottom: 10px; font-family: sans-serif; font-size: 14px; color: #7c2d12;">
                                            <strong>Pick-up Location:</strong> <span style="text-transform: capitalize;">{pickup_location}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="font-family: sans-serif; font-size: 14px; color: #7c2d12;">
                                            <strong>Payment Method:</strong> {payment_method}
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin: 0; font-family: sans-serif; font-size: 15px; line-height: 1.6; color: #4a5568;">
                                    If you have any changes or questions regarding your order, reply directly to this email. See you soon!
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td align="center" style="background-color: #f8fafc; padding: 20px; border-top: 1px solid #e2e8f0;">
                                <p style="margin: 0; font-family: sans-serif; font-size: 12px; color: #94a3b8;">
                                    © 2026 cookies4cuties. All rights reserved.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    text_body = f"""
    Hello!

    Thank you for ordering from Cookies4Cuties.

    We've received your order.

    ORDER SUMMARY
    ----------------------------

    {chr(10).join(item_rows_text)}

    Total: PHP {total_price}

    ORDER DETAILS
    ----------------------------

    Order Status: {order_status}
    Pickup Location: {pickup_location}
    Payment Method: {payment_method}

    If you have questions regarding your order,
    you can reply directly to this email.

    Thank you for supporting Cookies4Cuties!
    """
    # Set a plain text fallback for email clients that do not support HTML
    msg.set_content(text_body)

    # Inject the styled HTML content
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
