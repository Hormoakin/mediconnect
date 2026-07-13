#!/usr/bin/env python3
"""
MediConnect — Integration Verification Scripts
Run each section to verify your API keys work.
Run from inside the backend container:
  docker exec -it mediconnect_backend python verify_integrations.py
Or locally (with venv activated):
  cd backend && python verify_integrations.py
"""
import os, sys
from dotenv import load_dotenv

load_dotenv()

def separator(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)

# ── 1. Twilio SMS Test ────────────────────────────────────────
def test_twilio():
    separator("TWILIO SMS TEST")
    try:
        from twilio.rest import Client
        account_sid  = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token   = os.getenv('TWILIO_AUTH_TOKEN')
        from_number  = os.getenv('TWILIO_PHONE_NUMBER')

        if not all([account_sid, auth_token, from_number]):
            print("❌  Missing Twilio env vars. Check .env file.")
            return

        client = Client(account_sid, auth_token)

        # Verify account is active
        account = client.api.v2010.accounts(account_sid).fetch()
        print(f"✅  Twilio Account: {account.friendly_name}")
        print(f"✅  Account Status: {account.status}")
        print(f"✅  From Number:    {from_number}")

        # Send a test SMS to your own phone number
        # Replace with YOUR personal phone number to receive the test
        test_phone = input("\n  Enter your phone number to receive test SMS (e.g. +2348012345678): ").strip()
        if test_phone:
            msg = client.messages.create(
                body="MediConnect test SMS ✅ — Twilio integration working!",
                from_=from_number,
                to=test_phone,
            )
            print(f"✅  SMS sent! SID: {msg.sid}")
            print(f"✅  Status: {msg.status}")
        else:
            print("⏭️  Skipped SMS send (no phone entered).")

    except Exception as e:
        print(f"❌  Twilio test failed: {e}")


# ── 2. SendGrid Email Test ────────────────────────────────────
def test_sendgrid():
    separator("SENDGRID EMAIL TEST")
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail

        api_key = os.getenv('SENDGRID_API_KEY')
        if not api_key:
            print("❌  Missing SENDGRID_API_KEY. Check .env file.")
            return

        sg = sendgrid.SendGridAPIClient(api_key=api_key)

        # Send a test email
        test_email = input("  Enter your email to receive test email: ").strip()
        if not test_email:
            print("⏭️  Skipped email send (no email entered).")
            return

        message = Mail(
            from_email=('noreply@mediconnect.salman-aak.com', 'MediConnect'),
            to_emails=test_email,
            subject='MediConnect — SendGrid Integration Test ✅',
            html_content="""
            <h2>MediConnect SendGrid Test</h2>
            <p>✅ Your SendGrid integration is working correctly.</p>
            <p>This email was sent from the MediConnect backend.</p>
            <hr>
            <small>MediConnect — mediconnect.salman-aak.com</small>
            """
        )
        response = sg.send(message)
        if response.status_code in (200, 201, 202):
            print(f"✅  Email sent! Status: {response.status_code}")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"    Body: {response.body}")

    except Exception as e:
        print(f"❌  SendGrid test failed: {e}")
        print("    Common fix: Verify your sender email in SendGrid dashboard.")
        print("    Go to: Settings → Sender Authentication → Verify a Single Sender")


# ── 3. OpenAI API Test ────────────────────────────────────────
def test_openai():
    separator("OPENAI API TEST")
    try:
        from openai import OpenAI

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌  Missing OPENAI_API_KEY. Check .env file.")
            return

        client = OpenAI(api_key=api_key)

        print("  Sending test symptom analysis to GPT-4...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": "Patient reports: headache, fever, and fatigue for 2 days. Respond in one sentence with the most likely condition."
            }],
            max_tokens=100,
        )
        result = response.choices[0].message.content
        print(f"✅  OpenAI GPT-4 response: {result}")
        print(f"✅  Model used:  {response.model}")
        print(f"✅  Tokens used: {response.usage.total_tokens}")

    except Exception as e:
        print(f"❌  OpenAI test failed: {e}")
        if "insufficient_quota" in str(e):
            print("    Fix: Add billing credit at platform.openai.com → Settings → Billing")
        elif "invalid_api_key" in str(e):
            print("    Fix: Check your API key in .env — it should start with sk-proj-...")


# ── 4. PostgreSQL Connection Test ─────────────────────────────
def test_postgres():
    separator("POSTGRESQL CONNECTION TEST")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=os.getenv('DATABASE_PORT', '5432'),
            dbname=os.getenv('DATABASE_NAME', 'mediconnect'),
            user=os.getenv('DATABASE_USER', 'mediconnect_user'),
            password=os.getenv('DATABASE_PASSWORD'),
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅  PostgreSQL connected!")
        print(f"✅  Version: {version[:50]}")
        conn.close()
    except Exception as e:
        print(f"❌  PostgreSQL failed: {e}")


# ── 5. Redis Connection Test ──────────────────────────────────
def test_redis():
    separator("REDIS CONNECTION TEST")
    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.ping()
        r.set('mediconnect_test', 'hello', ex=10)
        val = r.get('mediconnect_test')
        print(f"✅  Redis connected!")
        print(f"✅  Test value: {val.decode()}")
    except Exception as e:
        print(f"❌  Redis failed: {e}")


# ── Run all tests ─────────────────────────────────────────────
if __name__ == '__main__':
    print("\n🏥 MediConnect — Integration Verification")
    print("   Testing all external service connections...\n")

    test_postgres()
    test_redis()
    test_twilio()
    test_sendgrid()
    test_openai()

    separator("SUMMARY")
    print("  Check each ✅ / ❌ above.")
    print("  All green? → Run: docker compose up -d")
    print("  Then:       → python manage.py migrate")
    print("  Then:       → python manage.py createsuperuser")
    print()
