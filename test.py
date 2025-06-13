import os
import dropbox
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
dbx = dropbox.Dropbox(
    oauth2_access_token=ACCESS_TOKEN,
    app_key=APP_KEY,
    app_secret=APP_SECRET
)

res = dbx.users_get_current_account()
print(type(res.account_type), res.account_type.tag)