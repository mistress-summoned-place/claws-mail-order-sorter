#!/usr/bin/env python3
import sys
import os
import re
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr

# --- CONFIGURATION ---
IMAP_SERVER = "YOUR.IMAP.SERVER"
IMAP_PORT = 993 # Usually 993

# Your main login / mailbox credentials
IMAP_USER = "YOUR.MAIN.INBOX@domain.smth"
PASSWORD = "YOUR_PASSWORD"  # Or read from a secure file / pass / secret-tool. Nice idea, must look into this!

# The automated website address used for contact forms and WooCommerce
SITE_SYSTEM_EMAIL = "WEB-FORM-MAIL-ADDRESS@domain.smth"

BASE_FOLDER = "YOUR_CUSTOM_FOLDER"
SENT_FOLDER = "Sent"            # Adjust if your server uses "INBOX.Sent" or similar
WATCH_FILE = os.path.expanduser("~/.config/claws_active_orders.txt")


def decode_mime_words(s):
    """Decodes MIME-encoded headers (handles Estonian characters cleanly)."""
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    result = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            result.append(fragment.decode(encoding or "utf-8", errors="replace"))
        else:
            result.append(fragment)
    return "".join(result)


def sanitize_folder_name(name):
    """Cleans the customer name so it is safe for an IMAP folder path."""
    cleaned = re.sub(r'[/"\\*?<>|:]', '', name).strip()
    return cleaned if cleaned else "Unknown_Customer"


def extract_customer_from_file(filepath):
    """Reads the local Claws Mail cached email file and extracts customer details."""
    with open(filepath, "rb") as f:
        msg = email.message_from_binary_file(f)

    from_raw = decode_mime_words(msg.get("From", ""))
    to_raw = decode_mime_words(msg.get("To", ""))
    reply_to_raw = decode_mime_words(msg.get("Reply-To", ""))

    from_name, from_addr = parseaddr(from_raw)
    to_name, to_addr = parseaddr(to_raw)
    reply_name, reply_addr = parseaddr(reply_to_raw)

    # If the email is a system notification from your website address, pull the real customer from Reply-To
    if from_addr.lower() == SITE_SYSTEM_EMAIL.lower() and reply_addr:
        cust_name, cust_addr = reply_name, reply_addr
    elif from_addr.lower() == SITE_SYSTEM_EMAIL.lower():
        # Fallback if Reply-To isn't present on a site notification
        cust_name, cust_addr = to_name, to_addr
    else:
        # Standard direct email from a customer
        cust_name, cust_addr = from_name, from_addr

    if not cust_addr:
        sys.exit("Error: Could not find a valid customer email address in this message.")

    folder_label = sanitize_folder_name(cust_name) if cust_name else cust_addr.split("@")[0]
    return cust_addr.lower(), folder_label


def move_matching_messages(mail, source_folder, target_folder, customer_email):
    """Searches a folder for emails to/from the customer (including website Reply-To headers) and moves them."""
    status, _ = mail.select(f'"{source_folder}"')
    if status != "OK":
        return

    # Search query now checks FROM, TO, and the Reply-To header for website forms/WooCommerce
    search_query = f'(OR (OR (FROM "{customer_email}") (TO "{customer_email}")) (HEADER Reply-To "{customer_email}"))'
    status, data = mail.search(None, search_query)

    if status == "OK" and data[0]:
        msg_nums = data[0].split()
        for num in msg_nums:
            res, _ = mail.copy(num, f'"{target_folder}"')
            if res == "OK":
                mail.store(num, "+FLAGS", "\\Deleted")
        mail.expunge()


def register_watcher(customer_email, target_folder):
    """Saves the customer -> folder mapping for background syncing."""
    os.makedirs(os.path.dirname(WATCH_FILE), exist_ok=True)
    entries = {}
    if os.path.exists(WATCH_FILE):
        with open(WATCH_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    entries[k] = v

    entries[customer_email] = target_folder
    with open(WATCH_FILE, "w", encoding="utf-8") as f:
        for k, v in entries.items():
            f.write(f"{k}={v}\n")


def run_sync(customer_email, target_folder):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(IMAP_USER, PASSWORD)

    # Ensure parent 'Tellimused' and customer folder exist
    mail.create(f'"{BASE_FOLDER}"')
    mail.create(f'"{target_folder}"')

    # Sweep past messages from INBOX and Sent
    move_matching_messages(mail, "INBOX", target_folder, customer_email)
    move_matching_messages(mail, SENT_FOLDER, target_folder, customer_email)

    mail.logout()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: order_sorter.py <path_to_email_file> | --watch")

    if sys.argv[1] == "--watch":
        if not os.path.exists(WATCH_FILE):
            sys.exit(0)
        with open(WATCH_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    cust_email, folder = line.strip().split("=", 1)
                    run_sync(cust_email, folder)
    else:
        cust_email, folder_label = extract_customer_from_file(sys.argv[1])
        target_folder = f"{BASE_FOLDER}/{folder_label}"
        run_sync(cust_email, target_folder)
        register_watcher(cust_email, target_folder)
