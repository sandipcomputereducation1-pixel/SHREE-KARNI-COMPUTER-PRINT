SHREE KARNI COMPUTER DALOT – PRINT BY QR
Windows 11 + Mobile Hotspot + Canon PIXMA G3012

PACKAGE CONTENTS
- app.py: customer upload website + shop dashboard + QR + UPI details + agent API
- agent.py: Windows helper that checks cloud orders and opens new files for preview
- run_agent.bat: easy way to start the Windows helper
- render.yaml: starter deployment configuration
- requirements.txt

CURRENT SHOP DETAILS
Shop: Shree Karni Computer Dalot
Contacts: 7891411425 / 7339871128
UPI ID: 7891411425@ptyes
Printing flow: Preview first, operator presses Print manually.

IMPORTANT HONEST LIMITATIONS
1. This ZIP is the application source/starter. It is NOT yet published online; therefore no live public QR exists yet.
2. Online hosting needs an account and deployment. Follow deployment instructions below.
3. UPI ID is displayed as the payment destination. No automatic payment confirmation or dynamic amount is implemented. Verify payment in the shop's UPI app before marking Paid.
4. The Windows agent downloads new orders and opens them for preview. It does NOT silently print. Operator chooses Canon PIXMA G3012 and presses Print.
5. The sample Render setup may use temporary local storage. Do not accept important/private customer files until persistent storage, backups, HTTPS, authentication and automatic file expiry are configured.
6. Set strong ADMIN_PASSWORD, AGENT_TOKEN and SECRET_KEY before use. Never share these secrets.
7. Do not collect/store Aadhaar, PAN or other sensitive files longer than required.

DEPLOY SERVER (requires internet and a hosting account)
A. Put app.py, requirements.txt and render.yaml in a private GitHub repository.
B. Create a Web Service from that repository on a Python host such as Render.
C. Set environment variables:
   PUBLIC_URL = the HTTPS URL assigned by your host
   ADMIN_PASSWORD = a strong unique password
   AGENT_TOKEN = a long random secret (same value used by Windows agent)
   UPI_ID = 7891411425@ptyes
   SECRET_KEY = a long random secret
D. After deployment, visit https://YOUR-SITE/ and test with a harmless sample PDF.
E. Download the QR at /qr.png. Print it only after confirming it opens your live /upload page.

WINDOWS PC SETUP
1. Install Python 3.11 or newer on the shop PC; select "Add Python to PATH".
2. Extract this ZIP on the Windows PC.
3. Open Command Prompt in the extracted folder and run:
   py -m pip install -r requirements.txt
4. After server deployment, double-click run_agent.bat.
5. Enter the hosted HTTPS URL and the same AGENT_TOKEN.
6. Keep the PC connected to mobile hotspot and keep agent window running.
7. When an order arrives, its file opens. Preview it, then manually print using Canon PIXMA G3012.

ADMIN
Open https://YOUR-SITE/admin and sign in using ADMIN_PASSWORD.
Check the customer's requested print settings. Mark Paid only after confirming the UPI credit or receiving cash.

MOBILE HOTSPOT
The shop PC only needs outbound internet access to connect to the hosted service. Customers can scan the public QR using any internet connection. No router port forwarding is needed.
