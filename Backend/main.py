from googleapiclient.discovery import build

service = build("gmail", "v1", credentials=creds)

results = service.users().messages().list(userId="me", maxResults=10).execute()

messages = results.get("messages", [])
