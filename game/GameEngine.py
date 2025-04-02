import gymnasium as gym
import random 
import numpy as np 

class GameEngine:
    def __init__(self):
        """Initializes and starts a new Blackjack game."""
        self.env = gym.make("Blackjack-v1")
        self.suits = ['clubs','diamonds','hearts','spades']

        self._new_game()

    def step(self, action):
        """Regular Function used to return the next stage of the game """
        res = self.env.step(action)

        print("==== STEP DEBUG ====")
        print("Action:", action)
        print("Terminated:", res[2])
        print("Dealer Raw:", self.env.unwrapped.dealer)
        print("Dealer Sum:", np.sum(self.env.unwrapped.dealer))
        print("====================")

        self.refresh()

        self.player_hand_suit.append(random.choice(self.suits)) 
        
        return res

    def _new_game(self):
        """Resets the game environment and gets initial hands."""
        self.obs, _ = self.env.reset()
        self.refresh()
        self.player_hand_suit = random.choices(self.suits,k=2)

        self.dealer_hand_suit = random.choices(self.suits, k=10) # just sample some random stuffs here...for convenience sake

    def refresh(self):
        """ Refreshes the class state"""
        self.player_hand = self.env.unwrapped.player[:]
        self.dealer_hand = self.env.unwrapped.dealer[:]
        