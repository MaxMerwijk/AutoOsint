from modules import openrouter
from modules import config
import tls_client
import time
from typing import List, Dict, Optional
from datetime import datetime

class Discord:
    def __init__(self, config, user_id='', server_id='', channel_id='', amount=500):
        self.session = tls_client.Session(client_identifier='chrome_108')
        self.config = config
        self.user_id = user_id
        self.server_id = server_id
        self.channel_id = channel_id
        self.amount = amount
        self.messages = []
        self.headers = self.create_headers()
        self.max_retries = 3
        self.retry_delay = 2

    def create_headers(self) -> Dict[str, str]:
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en-NL;q=0.9,en-GB;q=0.8',
            'authorization': self.config['discordToken'],
            'sec-ch-ua': '"Not;A=Brand";v="24", "Chromium";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-GB',
            'x-discord-timezone': 'Europe/Amsterdam',
            'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEwOC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTA4LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjk5OTksImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
        }

    def get_discord_messages(self) -> List[Dict]:
        print(f"\n🔍 Initializing Discord message retrieval for user ID: {self.user_id}")
        print(f"📊 Target amount of messages: {self.amount}")
        self.messages = []
        offset = 0
        
        while len(self.messages) < self.amount:
            time.sleep(1)
            params = {
                'author_id': self.user_id,
                'limit': 25,
                'guild_id': self.server_id,
                'offset': offset
            }
            
            print(f"📥 Fetching messages (Batch {offset//25 + 1})...")
            
            result = self.make_request_with_retry(
                f'https://discord.com/api/v9/guilds/{self.server_id}/messages/search',
                params
            )
            
            if not result:
                print("❌ Failed to retrieve messages. Check your Discord token and permissions.")
                break
                
            messages = result.get('messages', [])
            if not messages:
                print("✅ No more messages available.")
                break
                
            batch_count = 0
            for message_group in messages:
                for message in message_group:
                    if message.get('author', {}).get('id') == self.user_id:
                        content = message.get('content', '').strip()
                        if content:
                            self.messages.append({
                                'content': content,
                                'timestamp': message.get('timestamp'),
                                'channel_id': message.get('channel_id'),
                                'attachments': message.get('attachments', [])
                            })
                            batch_count += 1
            
            print(f"✅ Retrieved {batch_count} messages in this batch")
            offset += len(messages)
            
            if batch_count == 0:
                print("📌 No new messages found in this batch")
                break
        
        print(f"\n📊 Total messages retrieved: {len(self.messages)}")
        return self.messages

    def get_discord_dms(self) -> List[Dict]:
        print(f"\n🔍 Initializing Discord DM retrieval for user ID: {self.user_id}")
        print(f"📊 Target amount of messages: {self.amount}")
        self.messages = []
        before = None
        
        while len(self.messages) < self.amount:
            time.sleep(1)
            url = f'https://discord.com/api/v9/channels/{self.channel_id}/messages'
            params = {
                'limit': 100
            }
            if before:
                params['before'] = before
            
            print(f"📥 Fetching DM messages...")
            
            result = self.make_request_with_retry(url, params)
            
            if not result:
                print("❌ Failed to retrieve DMs. Check your Discord token and permissions.")
                break
            
            if not result:  # If no messages are returned
                print("✅ No more DMs available.")
                break
            
            batch_count = 0
            for message in result:
                if message.get('author', {}).get('id') == self.user_id:
                    content = message.get('content', '').strip()
                    if content:
                        self.messages.append({
                            'content': content,
                            'timestamp': message.get('timestamp'),
                            'channel_id': message.get('channel_id'),
                            'attachments': message.get('attachments', [])
                        })
                        batch_count += 1
                
                if len(result) > 0:
                    before = result[-1]['id']
            
            print(f"✅ Retrieved {batch_count} DMs in this batch")
            
            if batch_count == 0 or len(result) == 0:
                print("📌 No new DMs found in this batch")
                break
        
        print(f"\n📊 Total DMs retrieved: {len(self.messages)}")
        return self.messages

    def make_request_with_retry(self, url: str, params: Dict) -> Optional[Dict]:
        for retry in range(self.max_retries):
            try:
                response = self.session.get(url, headers=self.headers, params=params)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    retry_after = response.json().get('retry_after', self.retry_delay)
                    print(f"⚠️ Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
                    time.sleep(self.retry_delay)
            except Exception as e:
                print(f"❌ Request failed: {str(e)}")
                time.sleep(self.retry_delay)
        return None


class Main:
    def __init__(self):
        print("\n🔧 Initializing AutoOSINT...")
        print("📚 Loading configuration...")
        self.config = config.Config().load()
        print("🤖 Setting up AI model...")
        self.openrouter = openrouter.Openrouter(self.config)
        self.discord = None

    def setup_discord(self, user_id: str, server_id: str = '', channel_id: str = '', amount: int = 500):
        self.discord = Discord(self.config, user_id=user_id, server_id=server_id, channel_id=channel_id, amount=amount)

    def display_menu(self):
        print("\n🔍 AutoOSINT Analysis Options:")
        print("1. Analyze Discord Channel Messages")
        print("2. Analyze Discord DMs")
        print("3. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

    def get_user_input(self, is_channel: bool = True):
        user_id = input("\nEnter target user ID: ").strip()
        amount = input("Enter number of messages to analyze (default 500): ").strip()
        amount = int(amount) if amount.isdigit() else 500

        if is_channel:
            server_id = input("Enter server ID: ").strip()
            return user_id, server_id, amount
        else:
            channel_id = input("Enter DM channel ID: ").strip()
            return user_id, channel_id, amount

    def format_messages(self, messages):
        if not messages:
            return "No messages available for analysis."
        
        formatted_data = []
        for msg in messages:
            timestamp = msg.get('timestamp', '')
            content = msg.get('content', '').strip()
            if content:
                formatted_data.append(f"[{timestamp}] {content}")
        
        return "\n".join(formatted_data)

    def run(self):
        try:
            while True:
                choice = self.display_menu()
                
                if choice == '3':
                    print("\n👋 Thank you for using AutoOSINT!")
                    break
                
                if choice == '1':
                    print("\n📊 Discord Channel Analysis Selected")
                    user_id, server_id, amount = self.get_user_input(is_channel=True)
                    self.setup_discord(user_id=user_id, server_id=server_id, amount=amount)
                    messages = self.discord.get_discord_messages()
                else:  # choice == '2'
                    print("\n📱 Discord DM Analysis Selected")
                    user_id, channel_id, amount = self.get_user_input(is_channel=False)
                    self.setup_discord(user_id=user_id, channel_id=channel_id, amount=amount)
                    messages = self.discord.get_discord_dms()

                if not messages:
                    print("❌ Error: No messages could be retrieved from Discord")
                    continue
                
                print(f"\n📊 Phase 2: Data Processing")
                print(f"📝 Processing {len(messages)} messages...")
                corpus = self.format_messages(messages)
                
                if not corpus:
                    print("❌ Error: No valid message content to analyze")
                    continue
                
                print("\n🧠 Phase 3: AI Analysis")
                print("🔄 Loading analysis framework...")
                prompt = config.Config().get_prompt()
                
                print("🤖 Generating psychological profile...")
                formatted_prompt = prompt.format(corpus=corpus)
                print("⚙️ Running AI analysis (this may take a few minutes)...")
                response = self.openrouter.get_completion(formatted_prompt)
                
                if response:
                    print("\n📋 Phase 4: Results")
                    print("✍️ Writing analysis to output.txt...")
                    
                    with open('output.txt', 'w', encoding='utf-8') as f:
                        f.write(response)
                    
                    print("\n✅ Analysis complete!")
                    print("📄 Results have been saved to output.txt")
                else:
                    print("❌ Error: Failed to get analysis from AI model")
        
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please check your configuration and try again.")


if __name__ == '__main__':
    Main().run()