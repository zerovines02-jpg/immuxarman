from flask import Flask, request, render_template_string
import requests
import os
import re
import time
import threading

app = Flask(__name__)

# Facebook के मुख्य पेज से CSRF टोकन (fb_dtsg) निकालने का फंक्शन
def get_fb_dtsg(session, cookies_dict):
    url = "https://www.facebook.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        res = session.get(url, headers=headers, cookies=cookies_dict, timeout=15)
        match = re.search(r'name="fb_dtsg" value="(.*?)"', res.text)
        if match:
            return match.group(1)
        
        match_alt = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', res.text)
        if match_alt:
            return match_alt.group(1)
    except Exception as e:
        print(f"[ERROR] fb_dtsg निकालने में विफलता: {e}")
    return None

# बैकग्राउंड में मैसेज भेजने की मुख्य प्रक्रिया
def send_messages_worker(cookie_type, single_cookie, cookies_list, thread_id, mn, time_interval, messages):
    selected_cookies = [single_cookie] if cookie_type == 'single' else cookies_list

    while True:
        try:
            for cookie_str in selected_cookies:
                cookie_str = cookie_str.strip()
                if not cookie_str:
                    continue

                cookies_dict = {}
                for item in cookie_str.split(';'):
                    if '=' in item:
                        k, v = item.strip().split('=', 1)
                        cookies_dict[k] = v

                session = requests.Session()
                fb_dtsg = get_fb_dtsg(session, cookies_dict)

                if not fb_dtsg:
                    print(f"[FAILED] इस कुकी से fb_dtsg प्राप्त नहीं हुआ: {cookie_str[:20]}...")
                    continue

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': f'https://www.facebook.com/messages/t/{thread_id}',
                }

                for msg_text in messages:
                    full_message = f"{mn} {msg_text}"
                    payload = {
                        'fb_dtsg': fb_dtsg,
                        'body': full_message,
                        'recipient_ids': thread_id,
                    }

                    try:
                        response = session.post(
                            'https://www.facebook.com/messaging/send/',
                            data=payload,
                            headers=headers,
                            cookies=cookies_dict,
                            timeout=10
                        )
                        if response.status_code == 200:
                            print(f"[SUCCESS] मैसेज भेजा गया: {full_message}")
                        else:
                            print(f"[FAILED] स्टेटस कोड {response.status_code}: मैसेज नहीं जा सका")
                    except Exception as req_err:
                        print(f"[ERROR] रिक्वेस्ट एरर: {req_err}")

                    time.sleep(time_interval)

        except Exception as global_err:
            print(f"[CRITICAL ERROR] लूप में त्रुटि: {global_err}")
            time.sleep(30)


@app.route('/', methods=['GET', 'POST'])
def index():
    # बैकग्राउंड इमेज URL यहाँ फिक्स कर दिया गया है
    pinterest_url = "https://i.pinimg.com/1200x/fd/02/61/fd02614171fb8ec0bafeae1966314ebb.jpg"
    status_msg = ""

    if request.method == 'POST':
        cookie_type = request.form.get('tokenType')
        single_cookie = request.form.get('accessToken', '')
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time', 5))

        # मैसेज फ़ाइल पढ़ना
        txt_file = request.files.get('txtFile')
        messages = txt_file.read().decode('utf-8').splitlines() if txt_file else []

        # मल्टी-कुकी फ़ाइल पढ़ना
        cookies_list = []
        if cookie_type == 'multi':
            token_file = request.files.get('tokenFile')
            if token_file:
                cookies_list = token_file.read().decode('utf-8').splitlines()

        # बैकग्राउंड थ्रेड स्टार्ट करना
        thread = threading.Thread(
            target=send_messages_worker,
            args=(cookie_type, single_cookie, cookies_list, thread_id, mn, time_interval, messages)
        )
        thread.daemon = True
        thread.start()

        status_msg = "Task started successfully in background!"

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Arman exit InSiDe❤️</title>
  <style>
    body {
      background-image: url('{{ pinterest_url }}');
      background-size: cover;
      background-repeat: no-repeat;
      background-attachment: fixed;
      background-position: center;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      padding: 20px 10px;
      color: #ffffff;
    }

    .header {
      text-align: center;
      padding: 15px;
      margin-bottom: 20px;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 15px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
      max-width: 450px;
      margin-left: auto;
      margin-right: auto;
    }
    
    .header h1 {
      font-size: 1.2rem;
      margin: 5px 0;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #ffffff;
      text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    
    .header p {
      font-size: 0.9rem;
      margin: 5px 0;
      color: #e0e0e0;
    }

    .container {
      max-width: 380px;
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-radius: 16px;
      padding: 25px;
      border: 1px solid rgba(255, 255, 255, 0.25);
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
      margin: 0 auto;
    }

    label {
      font-weight: 600;
      font-size: 0.85rem;
      margin-bottom: 5px;
      display: block;
      color: #ffffff;
      text-shadow: 0 1px 2px rgba(0,0,0,0.6);
    }

    .form-control {
      width: 100%;
      box-sizing: border-box;
      margin-bottom: 12px;
      padding: 10px;
      background: rgba(255, 255, 255, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 8px;
      color: #ffffff;
      font-size: 0.9rem;
      outline: none;
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
    }

    .form-control::placeholder {
      color: #dddddd;
    }

    .form-control option {
      background: #222222;
      color: #ffffff;
    }

    .btn-submit {
      width: 100%;
      margin-top: 10px;
      padding: 12px;
      background: rgba(0, 123, 255, 0.6);
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
      color: white;
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 8px;
      cursor: pointer;
      font-weight: bold;
      font-size: 1rem;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .btn-submit:hover {
      background: rgba(0, 123, 255, 0.85);
      transform: translateY(-2px);
    }

    .footer {
      text-align: center;
      margin-top: 20px;
      padding: 10px;
      background: rgba(0, 0, 0, 0.2);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      max-width: 380px;
      margin-left: auto;
      margin-right: auto;
    }

    .footer p {
      margin: 3px 0;
      font-size: 0.8rem;
      color: #d1d1d1;
    }

    .status-alert {
      color: #00ff7f;
      font-weight: bold;
      text-align: center;
      text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    }
  </style>
</head>
<body>
  <header class="header">
    <h1> 𝙾𝙵𝙵𝙻𝙸𝙽𝙴 𝚂𝙴𝚁𝚅𝙴𝚁 <br> MADE BY THE EXIT ARMAN🤍</h1>
    <p>BOLO LEGENDS KA BAAP ARMAN ZINDABAD >3:)</p>
    <h1>🅾🆆🅽🅴🆁]|I{•------» EXIT ARM4N ON FIRE ❤️</h1>
  </header>

  <div class="container">
    {% if status_msg %}
      <p class="status-alert">{{ status_msg }}</p>
    {% endif %}
    <form action="/" method="post" enctype="multipart/form-data">
      <div class="mb-3">
        <label for="tokenType">Select Cookie Type:</label>
        <select class="form-control" id="tokenType" name="tokenType" required>
          <option value="single">Single Cookie</option>
          <option value="multi">Multi Cookie</option>
        </select>
      </div>
      <div class="mb-3" id="singleCookieBox">
        <label for="accessToken">Enter Your Cookie String:</label>
        <input type="text" class="form-control" id="accessToken" name="accessToken" placeholder="c_user=...; xs=...;">
      </div>
      <div class="mb-3">
        <label for="threadId">Enter Convo/Inbox ID:</label>
        <input type="text" class="form-control" id="threadId" name="threadId" required>
      </div>
      <div class="mb-3">
        <label for="kidx">Enter Hater Name / Prefix:</label>
        <input type="text" class="form-control" id="kidx" name="kidx" required>
      </div>

      <div class="mb-3">
        <label for="txtFile">Select Message File (.txt):</label>
        <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
      </div>
      <div class="mb-3" id="multiTokenFile" style="display: none;">
        <label for="tokenFile">Select Cookie File (for multi-cookie):</label>
        <input type="file" class="form-control" id="tokenFile" name="tokenFile" accept=".txt">
      </div>
      <div class="mb-3">
        <label for="time">Speed in Seconds:</label>
        <input type="number" class="form-control" id="time" name="time" value="5" required>
      </div>
      <button type="submit" class="btn-submit">Submit Your Details</button>
    </form>
  </div>
  <footer class="footer">
    <p>&copy; Developed by Arman BoY 2026. All Rights Reserved.</p>
    <p>Convo/Inbox Loader Tool</p>
  </footer>

  <script>
    document.getElementById('tokenType').addEventListener('change', function() {
      var tokenType = this.value;
      document.getElementById('multiTokenFile').style.display = tokenType === 'multi' ? 'block' : 'none';
      document.getElementById('singleCookieBox').style.display = tokenType === 'multi' ? 'none' : 'block';
    });
  </script>
</body>
</html>
    ''', pinterest_url=pinterest_url, status_msg=status_msg)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
