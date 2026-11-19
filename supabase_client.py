import os

import supabase
from supabase_auth import SyncSupportedStorage
from flask import session
class FlaskSessionStorage(SyncSupportedStorage):

    def get_item(self, key):
        return session.get(key)

    def set_item(self, key, value):
        session[key] = value

    def remove_item(self, key):
        session.pop(key, None)

def get_supabase():
    clientoptions = supabase.ClientOptions(flow_type="pkce", storage=FlaskSessionStorage())
    client = supabase.create_client(supabase_url=os.environ["PROJECT_LINK"], supabase_key=os.environ["SUPABASE_PUBLISHABLE_KEY"], options=clientoptions)
    return client



