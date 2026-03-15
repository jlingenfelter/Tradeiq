"""Email notification service using Klaviyo API."""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.wealth import WealthSnapshot
from app.models.alert import AlertSubscription

def _get_klaviyo():
    """Build a Klaviyo API client from settings."""
    from klaviyo_api import KlaviyoAPI
    return KlaviyoAPI(settings.KLAVIYO_API_KEY)


def send_email(to: str, subject: str, html_body: str) -> dict:
    """Send a transactional email via Klaviyo."""
    klaviyo = _get_klaviyo()

    # Use Klaviyo's event-based email sending
    event_payload = {
        "data": {
            "type": "event",
            "attributes": {
                "profile": {
                    "data": {
                        "type": "profile",
                        "attributes": {
                            "email": to,
                        },
                    },
                },
                "metric": {
                    "data": {
                        "type": "metric",
                        "attributes": {
                            "name": "Transactional Email",
                        },
                    },
                },
                "properties": {
                    "subject": subject,
                    "html_body": html_body,
                },
                "time": datetime.now(timezone.utc).isoformat(),
            },
        },
    }

    try:
        klaviyo.Events.create_event(event_payload)
        return {"status": "sent", "to": to, "subject": subject}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def send_weekly_recap(db: Session, user: User) -> dict:
    """Compile and send a weekly net worth recap email."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Get current and week-ago snapshots
    latest = db.query(WealthSnapshot).filter(
        WealthSnapshot.user_id == user.id,
    ).order_by(WealthSnapshot.snapshot_time.desc()).first()

    previous = db.query(WealthSnapshot).filter(
        WealthSnapshot.user_id == user.id,
        WealthSnapshot.snapshot_time <= week_ago,
    ).order_by(WealthSnapshot.snapshot_time.desc()).first()

    if not latest:
        return {"status": "skipped", "reason": "no_data"}

    current_nw = latest.net_worth
    prev_nw = previous.net_worth if previous else current_nw
    change = current_nw - prev_nw
    change_pct = (change / prev_nw * 100) if prev_nw != 0 else 0.0

    change_color = "#22c55e" if change >= 0 else "#ef4444"
    change_symbol = "+" if change >= 0 else ""

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 32px; border-radius: 12px;">
            <h1 style="color: #ffffff; font-size: 24px; margin: 0 0 8px 0;">Weekly Wealth Recap</h1>
            <p style="color: #94a3b8; margin: 0;">Week ending {now.strftime('%B %d, %Y')}</p>
        </div>

        <div style="padding: 24px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 16px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <p style="color: #64748b; font-size: 14px; margin: 0;">Net Worth</p>
                <p style="color: #1e293b; font-size: 36px; font-weight: 700; margin: 4px 0;">${current_nw:,.2f}</p>
                <p style="color: {change_color}; font-size: 18px; font-weight: 600; margin: 0;">
                    {change_symbol}${abs(change):,.2f} ({change_symbol}{abs(change_pct):.1f}%)
                </p>
            </div>

            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="padding: 12px 0; color: #64748b;">Total Assets</td>
                    <td style="padding: 12px 0; text-align: right; font-weight: 600;">${latest.total_assets:,.2f}</td>
                </tr>
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="padding: 12px 0; color: #64748b;">Total Liabilities</td>
                    <td style="padding: 12px 0; text-align: right; font-weight: 600;">${latest.total_liabilities:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; color: #64748b;">Liquid Net Worth</td>
                    <td style="padding: 12px 0; text-align: right; font-weight: 600;">${latest.liquid_net_worth:,.2f}</td>
                </tr>
            </table>
        </div>

        <div style="text-align: center; padding: 24px;">
            <a href="{settings.FRONTEND_URL}/dashboard" style="background: #6366f1; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                View Full Dashboard
            </a>
        </div>
    </div>
    """

    return send_email(
        to=user.email,
        subject=f"Your Weekly Recap: Net Worth {change_symbol}${abs(change):,.0f}",
        html_body=html,
    )


def send_alert_notification(db: Session, user: User, alert: dict) -> dict:
    """Send an alert notification email."""
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 32px; border-radius: 12px;">
            <h1 style="color: #ffffff; font-size: 24px; margin: 0;">Alert Notification</h1>
        </div>

        <div style="padding: 24px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 16px;">
            <div style="padding: 16px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 4px;">
                <p style="font-weight: 600; color: #92400e; margin: 0 0 4px 0;">{alert.get('title', 'Alert')}</p>
                <p style="color: #78350f; margin: 0;">{alert.get('message', '')}</p>
            </div>
        </div>

        <div style="text-align: center; padding: 24px;">
            <a href="{settings.FRONTEND_URL}/dashboard" style="background: #6366f1; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                View Dashboard
            </a>
        </div>
    </div>
    """

    return send_email(
        to=user.email,
        subject=f"TradeIQ Alert: {alert.get('title', 'Notification')}",
        html_body=html,
    )
