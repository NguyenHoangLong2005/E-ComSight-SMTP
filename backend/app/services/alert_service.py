"""
E-ComSight — Email Alert Service
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


URGENCY_CONFIG = {
    "critical": {"color": "#ef4444", "icon": "🔴", "label": "Nghiêm trọng"},
    "high":     {"color": "#f97316", "icon": "🟠", "label": "Cao"},
    "medium":   {"color": "#eab308", "icon": "🟡", "label": "Trung bình"},
    "low":      {"color": "#22c55e", "icon": "🟢", "label": "Thấp"},
}


def send_alert_email(
    to_email: str,
    alert_title: str,
    alert_message: str,
    urgency: str,
    review_comment: str = "",
    product_name: str = "",
    platform: str = "",
) -> bool:
    """Gửi email cảnh báo khi phát hiện review tiêu cực nghiêm trọng"""

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP chưa cấu hình — bỏ qua gửi email")
        return False

    cfg = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["medium"])

    html = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); padding: 24px; color: white; }}
  .header h1 {{ margin: 0; font-size: 22px; }}
  .header p {{ margin: 4px 0 0; opacity: 0.85; font-size: 14px; }}
  .badge {{ display: inline-block; background: {cfg["color"]}; color: white; padding: 4px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; }}
  .content {{ padding: 28px; }}
  .alert-box {{ background: #fef2f2; border-left: 4px solid {cfg["color"]}; padding: 16px; border-radius: 6px; margin: 16px 0; }}
  .review-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0; }}
  .review-box blockquote {{ margin: 0; font-style: italic; color: #64748b; }}
  .meta {{ font-size: 13px; color: #94a3b8; margin-top: 8px; }}
  .footer {{ background: #f8fafc; padding: 16px 28px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #94a3b8; }}
  .btn {{ display: inline-block; background: #1e40af; color: white; text-decoration: none; padding: 10px 24px; border-radius: 6px; font-weight: 600; margin-top: 16px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>⚡ E-ComSight — Cảnh báo Phản hồi</h1>
    <p>Phát hiện tự động lúc {datetime.now().strftime("%H:%M ngày %d/%m/%Y")}</p>
  </div>
  <div class="content">
    <p>Xin chào,</p>
    <p>Hệ thống <strong>E-ComSight</strong> phát hiện phản hồi tiêu cực cần xử lý ngay:</p>

    <div class="alert-box">
      <p style="margin:0 0 8px;">
        <span class="badge">{cfg["icon"]} {cfg["label"].upper()}</span>
      </p>
      <h2 style="margin:8px 0; color:#1e293b; font-size:18px;">{alert_title}</h2>
      <p style="margin:0; color:#475569;">{alert_message}</p>
    </div>

    {"" if not review_comment else f'''
    <div class="review-box">
      <p style="margin:0 0 8px; font-weight:600; color:#1e293b;">💬 Nội dung review:</p>
      <blockquote>"{review_comment}"</blockquote>
      <div class="meta">
        {f"📦 Sản phẩm: {product_name}" if product_name else ""}
        {f" &nbsp;|&nbsp; 🛒 Platform: {platform.capitalize()}" if platform else ""}
      </div>
    </div>
    '''}

    <p>Bạn nên <strong>kiểm tra và phản hồi khách hàng sớm nhất có thể</strong> để bảo vệ uy tín cửa hàng.</p>
    <a href="https://huggingface.co/spaces/hoanglongnguyen/ecomsight" class="btn">→ Xem trên Dashboard</a>
  </div>
  <div class="footer">
    E-ComSight · Học viện Ngân hàng · Data for Impact 2026<br>
    Email này được gửi tự động. Vui lòng không trả lời.
  </div>
</div>
</body>
</html>
"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{cfg['icon']} [E-ComSight] {alert_title}"
        msg["From"] = f"E-ComSight <{settings.SMTP_USER}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_email, msg.as_string())

        logger.info(f"✅ Alert email gửi thành công → {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed — kiểm tra App Password Gmail")
        return False
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False
