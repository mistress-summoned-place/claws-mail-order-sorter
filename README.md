# Claws Mail Order & Thread Sorter

A lightweight Python automation script for **Claws Mail** (and IMAP servers) that automatically groups related customer emails and replies into dedicated project/order folders under a unified parent directory (e.g., `BASE_FOLDER = "YOUR_CUSTOM_FOLDER"`).


## Why This Exists
Claws Mail is fast, minimalist, and keeps a clean threaded view, but lacks native virtual folders or advanced automated tagging. When running an independent artisan studio, managing customer inquiries, contact form submissions, and WooCommerce orders alongside direct emails can quickly lead to inbox clutter.

This script solves that by:
1. Extracting the real customer identity from direct emails or website notifications.
2. Leveraging the **`Reply-To`** header to correctly identify customers even when notifications originate from a site system address (`WEB-FORM-MAIL-ADDRESS@domain.smth`).
3. Creating a dedicated IMAP folder for that customer and sweeping all past and future thread correspondence into it.
4. Providing a background `--watch` mode to continuously sync active threads via cron.


---

## Features
- **Smart Header Parsing:** Automatically falls back to `Reply-To` headers for automated web forms and WooCommerce order notifications.
- **Thread Sweeping:** Grabs incoming mail, system alerts, and your own sent replies from your unified `INBOX`.
- **Zero bloat:** Pure Python standard libraries (`imaplib`, `email`, `re`), requiring zero heavy dependencies.
- **Background Watcher:** Tracks active orders locally so cron can keep folders updated automatically.

---


## Installation & Setup

### 1. Requirements
- Python 3.x
- Claws Mail with IMAP account configuration

### 2. Configuration
Download or copy `claws-mail_order-sorter-incl-reply-to.py` and fill in your server details, credentials, and system email at the top of the file:

    IMAP_SERVER = "YOUR.IMAP.SERVER"
    IMAP_PORT = 993
    IMAP_USER = "YOUR.MAIN.INBOX@domain.smth"
    PASSWORD = "YOUR_PASSWORD"
    SITE_SYSTEM_EMAIL = "WEB-FORM-MAIL-ADDRESS@domain.smth" # Set if using contact forms/WooCommerce
    BASE_FOLDER = "YOUR_CUSTOM_FOLDER"


### 3. Claws Mail Action Setup
In Claws Mail, go to **Configuration -> Actions...*** and add a new action:

    Menu Name: New Order!

    Command: python3 /path/to/claws-mail_order-sorter-incl-reply-to.py %f

Now you can right-click any email, select your Action, and instantly build the customer's folder and sync the thread!

### 3. Background Cron Watcher (Optional)
To keep active threads automatically synced every few minutes without manual triggers, open your user crontab:

    crontab -e

Add the following line to run the watcher quietly every 5 minutes:

    */5 * * * * /path/to/order_sorter.py --watch >/dev/null 2>&1


## License

MIT License - feel free to use, modify, and adapt it for your own workflow. 

## Acknowledgements
Developed with the assistance of Gemini as a personal AI collaborator, tailored for clean IMAP workflows and minimal Linux environments.