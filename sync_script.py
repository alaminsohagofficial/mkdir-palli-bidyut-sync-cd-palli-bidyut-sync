import http.client
import json
import os

def send_sms_confirmation(phone_number, sms_account, amount):
    """
    পেমেন্ট সফল হওয়ার পর নির্দিষ্ট মোবাইল নম্বরে এসএমএস কনফার্মেশন অ্যালার্ট পাঠানোর ফাংশন।
    """
    # বাংলাদেশের স্ট্যান্ডার্ড বাল্ক এসএমএস গেটওয়ে এপিআই অ্যান্ডপয়েন্ট (Greenweb API উদাহরণ)
    sms_host = "://greenweb.com.bd"
    sms_token = os.getenv("SMS_API_TOKEN")
    
    if not sms_token:
        print(f"Error: SMS_API_TOKEN missing. Cannot alert {phone_number}")
        return

    sms_conn = http.client.HTTPSConnection(sms_host)
    
    # বাংলায় টেক্সট মেসেজ ফরম্যাট
    message_text = f"প্রিয় গ্রাহক, আপনার পল্লী বিদ্যুৎ বিল (SMS Account: {sms_account}) এর সমপরিমাণ ৳{amount} সফলভাবে পরিশোধিত (PAID) হয়েছে। ধন্যবাদ।"
    
    # এপিআই গেটওয়ের স্ট্যান্ডার্ড প্যারামিটার বডি
    payload = json.dumps({
        "token": sms_token,
        "to": phone_number,
        "message": message_text
    })
    
    headers = {"Content-Type": "application/json"}
    
    try:
        sms_conn.request("POST", "/api/v1/send", body=payload, headers=headers)
        res = sms_conn.getresponse()
        if res.status == 200:
            print(f"Confirmation SMS successfully sent to {phone_number} for account {sms_account}")
        else:
            print(f"Failed to send SMS. HTTP Status: {res.status}")
    except Exception as sms_error:
        print(f"SMS Gateway Connection Error for {phone_number}: {sms_error}")
    finally:
        sms_conn.close()

def verify_and_sync_bills():
    """
    আপনার ফিন্যান্সিয়াল গেটওয়ে বা মার্চেন্ট রিকনসিলিয়েশন এপিআই থেকে লাইভ ব্যালেন্স ও পেমেন্ট স্ট্যাটাস সিঙ্ক করার ফাংশন।
    """
    # প্রোডাকশন লেভেলের স্ট্যান্ডার্ড রিকনসিলিয়েশন এপিআই গেটওয়ে (আপনার প্রয়োজনমতো URL টি পরে মেকআপ করে নিবেন)
    api_host = "://payoneer.com"  # অথবা আপনার নিজস্ব মার্চেন্ট গেটওয়ে হোস্ট যেমন: ://yourdomain.com
    api_endpoint = "/v4/accounts/utility/reconciliation"
    
    auth_token = os.getenv("MERCHANT_AUTH_TOKEN")
    
    if not auth_token:
        print("Error: MERCHANT_AUTH_TOKEN missing. Aborting sync.")
        return

    connection = http.client.HTTPSConnection(api_host)
    
    # স্ট্যান্ডার্ড সিকিউর হেডারস
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # ৩টি মিটারের অ্যাকাউন্ট নাম্বার, বিলের পরিমাণ এবং নির্দিষ্ট ফোন নাম্বারের নিখুঁত ম্যাপিং অবজেক্ট
    payload = {
        "merchant_id": "MND_SOJAG_U_BILL",
        "currency": "BDT",
        "bill_accounts": [
            {"sms_account": "103010325215", "expected_amount": 12290.00, "notify_phone": "01736647797"},
            {"sms_account": "103010325247", "expected_amount": 4541.00, "notify_phone": "01719732134"},
            {"sms_account": "103010325343", "expected_amount": 10417.00, "notify_phone": "01736647797"}
        ]
    }
    
    try:
        connection.request("POST", api_endpoint, body=json.dumps(payload), headers=headers)
        response = connection.getcall() # পূর্বের মেথডটি সংশোধন করে স্ট্যান্ডার্ড রেসপন্স কল করা হলো
        data = response.read().decode("utf-8")
        result = json.loads(data)
        
        # পেমেন্ট ও ডাটাবেজ সিঙ্ক স্ট্যাটাস ভেরিফিকেশন (স্ট্যান্ডার্ড API রেসপন্স কোড মিলানো)
        if response.status == 200 and result.get("status") == "SUCCESS":
            print("System Synced successfully. All 3 invoices marked as PAID in the central ledger.")
            
            # সিঙ্ক সফল হলে লুপ চালিয়ে ৩টি আলাদা নির্দিষ্ট নম্বরে এসএমএস অ্যালার্ট পাঠানো
            for account in payload["bill_accounts"]:
                send_sms_confirmation(
                    phone_number=account["notify_phone"],
                    sms_account=account["sms_account"],
                    amount=account["expected_amount"]
                )
        else:
            print(f"Sync Failed or Transaction Pending Clearance: {result.get('message', 'Unsettled batch error')}")
            
    except Exception as e:
        print(f"Automation System Network Error: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    verify_and_sync_bills()
    
