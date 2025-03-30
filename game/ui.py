import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time 
import os 

# Black Jack Env
from GameEngine import GameEngine

class BlackjackUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blackjack RL - SDSC6007")
        self.root.geometry("1400x900")

        # Load the background image
        self.original_bg = Image.open("images/background.gif")

        # Load card images 
        self.card_images = self.load_card_images("images")
        
        # Coins / Props 
        self.coin_image_red = self._load_coin_image("images/coins.png", (40, 40))
        self.coin_image_blue = self._load_coin_image("images/blue-chip.png", (40, 40))

        # Game Status Mapper: 
        self.status_mapper = {1:'You Won!', 
                              0: 'You Lost...'}
        
        # Avatars 
        self.avatars = self.load_avatar("images")

        # Bills
        # self.bills = self._load_coin_image("images/bills.png", (200, 200))

        # Game engine
        self.engine = GameEngine()
        self.obs = self.engine.obs

        # Layout
        self.setup_layout()

        # utils
        self.rank_map = {1: 'ace'}
        self.winnings = []

    def load_avatar(self, folder):
        images = {}
        for filename in os.listdir(folder):
            if filename.endswith(".png") and "avatar" in filename:
                path = os.path.join(folder, filename)
                img = Image.open(path).resize((250, 250))
                key = filename.replace(".png", "")
                images[key] = ImageTk.PhotoImage(img)
        return images


    def load_card_images(self, folder):
        images = {}
        for filename in os.listdir(folder):
            if filename.endswith(".png"):
                path = os.path.join(folder, filename)
                img = Image.open(path).resize((80, 120))
                key = filename.replace(".png", "")
                images[key] = ImageTk.PhotoImage(img)
        return images

    def _load_coin_image(self, path, size_tuples):
        img = Image.open(path).resize(size_tuples)
        return ImageTk.PhotoImage(img)

    def setup_layout(self):
        self.root.configure(bg="#dfe7e2")
        style = ttk.Style()
        style.theme_use("clam")

        # background 
        self.table_frame = ttk.Frame(self.root)
        self.table_frame.place(relx=0.01, rely=0.01, relwidth=0.6, relheight=0.98)
        self.table_canvas = tk.Canvas(self.table_frame, bg="black")
        self.table_canvas.pack(fill=tk.BOTH, expand=True)
        self.table_canvas.bind("<Configure>", self.resize_background)

        # logging console 
        self.log_frame = ttk.LabelFrame(self.root, text="Game Log")
        self.log_frame.place(relx=0.62, rely=0.63, relwidth=0.37, relheight=0.35)
        self.log_text = tk.Text(self.log_frame, height=20, bg="black", fg="white", font=("Roboto", 12))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Hit button
        self.hit_button = tk.Button(
            self.table_frame,
            text="Hit",
            bg="#e74c3c",
            fg="white",
            font=("Roboto", 20, "bold"),
            relief="flat",
            bd=10,
            highlightthickness=0
        )
        self.hit_button.place(relx=0.25, rely=0.92, relwidth=0.2, relheight=0.06)
        self.hit_button.config(command=lambda: self.handle_action(1))

        # Stay button
        self.stick_button = tk.Button(
            self.table_frame,
            text="Stay",
            bg="#2ecc71",
            fg="white",
            font=("Roboto", 20, "bold"),
            relief="flat",
            bd=10,
            highlightthickness=0
        )
        self.stick_button.place(relx=0.55, rely=0.92, relwidth=0.2, relheight=0.06)
        self.stick_button.config(command=lambda: self.handle_action(0))

        # Avatars 
        self.avatar_image_id = self.table_canvas.create_image(
            250, 100,  # x, y position within the canvas — adjust as needed
            anchor="ne",
            image=self.avatars['losing_streak_avatar']
        )

        # Keep a reference to avoid garbage collection
        self.table_canvas.image = self.avatars['losing_streak_avatar']
    
    def draw_game_state(self, event):
        """ This function is used to draw the game state at launch"""
        player_sum, dealer_card, usable_ace = self.obs
        info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
        self.refresh_layout(info_text, mode = 'sys')
        self.display_cards()

    def refresh_layout(self, info_text, mode = 'regular'):
        """ This function is used to refresh the gane state after launch"""

        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()

        # Clear canvas before drawing new info
        self.table_canvas.delete("state")

        if mode == 'sys':
            self.obs = self.engine.obs
            player_sum, dealer_card, usable_ace = self.obs
            info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
            self.create_text(canvas_width, canvas_height, info_text)
            
        else:
            self.create_text(canvas_width, canvas_height, info_text)

        self.display_cards()

    def display_cards(self):
        self.table_canvas.delete("player-cards")
        self.table_canvas.delete("dealer-cards")

        #-------------------------------------------------------# 
        # Loading Player Cards 

        player_hand = self.engine.player_hand  # Assuming these are tuples like (rank, suit)
        player_hand_suit = self.engine.player_hand_suit

        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()

        for i, rank in enumerate(player_hand):
        
            suit = player_hand_suit[i]
            rank = self.rank_map.get(rank, rank)

            file_name = f"{rank}_of_{suit}"
            img = self.card_images[file_name]
            self.table_canvas.create_image(canvas_width/2 - len(player_hand) * 50 + i * canvas_width/8, 
                                            canvas_height / 1.5, 
                                            anchor=tk.NW, 
                                            image=img, 
                                            tags="player-cards")
            
        #-------------------------------------------------------# 
        # Loading Dealer Top Card

        dealer_hand = self.engine.dealer_hand[0]  # Assuming these are tuples like (rank, suit)
        dealer_hand_suit = self.engine.dealer_hand_suit[0]
        rank = self.rank_map.get(dealer_hand, dealer_hand)

        for i, f in enumerate([f"{rank}_of_{dealer_hand_suit}", "back"]):
            self.table_canvas.create_image(canvas_width/2 - 100 + i * canvas_width/8, 
                                            canvas_height / 8, 
                                            anchor=tk.NW, 
                                            image=self.card_images[f], 
                                            tags="dealer-cards")
    def logger(self, logs):
        self.log_text.insert(tk.END, logs)
        self.log_text.see(tk.END)

    def dealer_reveal(self, revealed_cards):
        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()
        dealer_hand_suit = self.engine.dealer_hand_suit
        buffer = 100

        job_list = []
        for idx, rank in enumerate(revealed_cards):
            rank = self.rank_map.get(rank, rank)
            job_list.append(f"{rank}_of_{dealer_hand_suit[idx]}")

        if len(job_list) < len(dealer_hand_suit):
            job_list.append("back")

        if len(job_list)>2:
            self.table_canvas.delete("dealer-cards")
            buffer = 210

        print(job_list)

        for i, f in enumerate(job_list):
            self.table_canvas.create_image(canvas_width/2 - buffer + i * canvas_width/8, 
                                            canvas_height / 8, 
                                            anchor=tk.NW, 
                                            image=self.card_images[f], 
                                            tags="dealer-cards")

    def handle_action(self, action):
        """
        This function is the main game loop.

        Parameters:
        ---
        Handles user actions: 0 = Hit, 1 = Stay
        
        """

        # Step through the game with the user action
        obs, reward, terminated, truncated, _ = self.engine.step(action)
        player_sum, dealer_card = obs[0], obs[1]

        # Display player's current state
        info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
        self.refresh_layout(info_text)

        # If the game is over due to busting
        if action == 1 and terminated and player_sum > 21:
            # self.log_text.insert(tk.END, f"Game Over — BUST! (Reward: {reward})\n")
            # self.log_text.see(tk.END)
            self.logger(f"Game Over — BUST! (Reward: {reward})\n")

            self.winnings.append(reward)

            self.engine._new_game()
            info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
            self.refresh_layout(info_text, mode='sys')

        # If terminated, show dealer's full hand one card at a time (with delay)
        if terminated and player_sum <= 21:
            self.hit_button.config(state="disabled")
            self.stick_button.config(state="disabled")
            
            # self.log_text.insert(tk.END, "\nDealer's Hand Revealed:\n")
            # self.log_text.see(tk.END)
            self.logger("\nDealer's Hand Revealed:\n")

            revealed_cards = []
            for idx, card in enumerate(self.engine.dealer_hand):
                revealed_cards.append(card)

                # Update canvas with new dealer info
                dealer_hand_text = ", ".join(str(c) for c in revealed_cards)
                info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_hand_text}"
                self.refresh_layout(info_text)
                self.dealer_reveal(revealed_cards)

                # Log each card
                # self.log_text.insert(tk.END, f"{card}\n")
                # self.log_text.see(tk.END)
                self.logger(f"{card}\n")

                self.root.update()
                time.sleep(1.5)

            # Show game result
            result_text = self.status_mapper.get(reward, 'Push (draw)')
            self.winnings.append(reward)

            # self.log_text.insert(tk.END, f"\nGame Over — {result_text} (Reward: {reward})\n")
            # self.log_text.see(tk.END)
            self.logger(f"\nGame Over — {result_text} (Reward: {reward})\n")
            
            self.engine._new_game()
            time.sleep(0.5)
            self.refresh_layout(info_text, mode='sys')

        self.hit_button.config(state="active")
        self.stick_button.config(state="active")

        self.logger(f"{'--'}"*50 + '\n')
        return True

    def create_text(self, canvas_width, canvas_height, info_text):
        self.table_canvas.create_text(
                canvas_width / 3,
                canvas_height / 2,
                text=info_text,
                font=("Roboto", 18, "bold"),
                fill="white",
                tags="state"
            )

    def resize_background(self, event):
        resized = self.original_bg.resize((event.width, event.height))
        self.bg_image = ImageTk.PhotoImage(resized)

        self.table_canvas.delete("all")
        self.table_canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="background")

        # Coins
        self.table_canvas.create_image(event.width/8, event.height/6, anchor=tk.CENTER, image=self.coin_image_blue, tags="coin")
        self.table_canvas.create_image(event.width/8 + 50, event.height/6, anchor=tk.CENTER, image=self.coin_image_red, tags="coin")
        self.table_canvas.create_image(event.width - 200, event.height - 150, anchor=tk.CENTER, image=self.coin_image_blue, tags="coin")
        self.table_canvas.create_image(event.width - 200 + 50, event.height - 150 , anchor=tk.CENTER, image=self.coin_image_red, tags="coin")

        # Bills
        # self.table_canvas.create_image(event.width/2, event.height/2, anchor=tk.CENTER, image=self.bills, tags="bills")

        # Observation display
        self.draw_game_state(event)


if __name__ == "__main__":
    root = tk.Tk()
    app = BlackjackUI(root)
    root.mainloop()
