"""Email service via Resend."""
import os

import resend

resend.api_key = os.getenv("RESEND_API_KEY", "")

FROM_ADDRESS = os.getenv("EMAIL_FROM", "noreply@fab.limited")
APP_URL = os.getenv("APP_URL", "http://localhost:5173")


def _send(to: str, subject: str, html: str) -> None:
    if not resend.api_key:
        print(f"[email] RESEND_API_KEY not set — would send to {to}: {subject}")
        return
    resend.Emails.send({"from": FROM_ADDRESS, "to": to, "subject": subject, "html": html})


def send_invite(to: str, name: str, company_name: str, temp_password: str) -> None:
    login_url = f"{APP_URL}/login"
    _send(
        to=to,
        subject=f"{company_name} — Platform Davetiyeniz",
        html=f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#fff">
          <div style="margin-bottom:24px">
            <span style="font-weight:700;font-size:18px">fab</span><span style="color:#888;font-size:18px">.engineering</span>
          </div>
          <h2 style="margin:0 0 8px;font-size:20px">Merhaba {name},</h2>
          <p style="color:#555;margin:0 0 24px;line-height:1.6">
            <strong>{company_name}</strong> platformuna davet edildiniz.
            Aşağıdaki geçici şifreyle giriş yapın ve şifrenizi değiştirin.
          </p>
          <div style="background:#f8f8f8;border:1px solid #e5e5e5;border-radius:8px;padding:20px 24px;margin:0 0 24px;text-align:center">
            <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Geçici Şifreniz</div>
            <div style="font-size:28px;font-weight:700;letter-spacing:4px;font-family:monospace;color:#0f172a">{temp_password}</div>
            <div style="font-size:12px;color:#f59e0b;margin-top:8px">⏱ 30 dakika geçerlidir</div>
          </div>
          <a href="{login_url}"
             style="display:inline-block;background:#0f172a;color:#fff;padding:12px 28px;
                    border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">
            Giriş Yap →
          </a>
          <p style="color:#aaa;font-size:12px;margin-top:24px;line-height:1.5">
            E-posta adresiniz: <strong>{to}</strong><br>
            Süre dolarsa giriş sayfasında otomatik olarak yeni şifre gönderilir.
          </p>
        </div>
        """,
    )


def send_temp_password(to: str, name: str, temp_password: str) -> None:
    """Send a freshly regenerated temp password (expired invite retry)."""
    login_url = f"{APP_URL}/login"
    _send(
        to=to,
        subject="Yeni Geçici Şifreniz",
        html=f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#fff">
          <div style="margin-bottom:24px">
            <span style="font-weight:700;font-size:18px">fab</span><span style="color:#888;font-size:18px">.engineering</span>
          </div>
          <h2 style="margin:0 0 8px;font-size:20px">Merhaba {name},</h2>
          <p style="color:#555;margin:0 0 24px;line-height:1.6">
            Önceki geçici şifrenizin süresi dolmuştu. Yeni geçici şifreniz:
          </p>
          <div style="background:#f8f8f8;border:1px solid #e5e5e5;border-radius:8px;padding:20px 24px;margin:0 0 24px;text-align:center">
            <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Yeni Geçici Şifreniz</div>
            <div style="font-size:28px;font-weight:700;letter-spacing:4px;font-family:monospace;color:#0f172a">{temp_password}</div>
            <div style="font-size:12px;color:#f59e0b;margin-top:8px">⏱ 30 dakika geçerlidir</div>
          </div>
          <a href="{login_url}"
             style="display:inline-block;background:#0f172a;color:#fff;padding:12px 28px;
                    border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">
            Giriş Yap →
          </a>
        </div>
        """,
    )


def send_admin_reset(to: str, name: str, temp_password: str) -> None:
    """Admin-initiated password reset — sends new temp password."""
    login_url = f"{APP_URL}/login"
    _send(
        to=to,
        subject="Şifre Sıfırlama",
        html=f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#fff">
          <div style="margin-bottom:24px">
            <span style="font-weight:700;font-size:18px">fab</span><span style="color:#888;font-size:18px">.engineering</span>
          </div>
          <h2 style="margin:0 0 8px;font-size:20px">Merhaba {name},</h2>
          <p style="color:#555;margin:0 0 24px;line-height:1.6">
            Yöneticiniz şifrenizi sıfırladı. Aşağıdaki geçici şifreyle giriş yapın.
          </p>
          <div style="background:#f8f8f8;border:1px solid #e5e5e5;border-radius:8px;padding:20px 24px;margin:0 0 24px;text-align:center">
            <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Geçici Şifreniz</div>
            <div style="font-size:28px;font-weight:700;letter-spacing:4px;font-family:monospace;color:#0f172a">{temp_password}</div>
            <div style="font-size:12px;color:#f59e0b;margin-top:8px">⏱ 30 dakika geçerlidir</div>
          </div>
          <a href="{login_url}"
             style="display:inline-block;background:#0f172a;color:#fff;padding:12px 28px;
                    border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">
            Giriş Yap →
          </a>
        </div>
        """,
    )
