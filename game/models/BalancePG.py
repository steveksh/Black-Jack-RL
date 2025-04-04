import torch
import torch.nn as nn

import numpy as np
from collections import defaultdict

class BalancePG(nn.Module):
    def __init__(self, state_dim, action_dim, money):
        super(BalancePG, self).__init__()

        self.money = money
        self.fnn = nn.Sequential(
            nn.Linear(state_dim, 32),
            nn.LeakyReLU(),
            nn.Linear(32, 2),
            nn.Softmax()
        )

        # storing the log probability distribution
        self.log_probabilities = []
        
        # storing the rewards for each step
        self.rewards = []

    def reset(self):
        """ Internal reset """
        self.log_probabilities = []
        self.rewards = []

    def forward(self, state):
        action_logits = self.fnn(state)

        return action_logits
    
    def tensor(self, obs):
        return torch.FloatTensor(obs)
    
    @torch.no_grad()
    def predict(self, obs):
        obs_tensor = self.tensor(obs)
        probs = self.fnn(obs_tensor)
        action = torch.argmax(probs).item()
        return action

    def generate_q_table(self, usable_ace=False, starting_pos=12):
        """Generate a tabular Q-value dict for plotting."""
        self.q_values = {}
        for player_sum in range(starting_pos, 22):
            for dealer_card in range(1, 11):
                state = (player_sum, dealer_card, usable_ace, self.money)
                state_tensor = self.tensor(state)
                q_vals = self.predict(state_tensor)
                self.q_values[state[:3]] = q_vals

def generate_policy(policy_net, money):
    policy_data = defaultdict(lambda: np.zeros(2))

    for player_sum in range(1, 22):           # 1 to 21
        for dealer_card in range(1, 11):      # 1 (Ace) to 10
            for usable_ace in [0, 1]:
                state = (player_sum, dealer_card, usable_ace, money)

                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    action_probs = policy_net(state_tensor).squeeze().numpy()

                policy_data[state] = np.argmax(action_probs)

    # Save as JSON
    serializable = {str(k): v.tolist() for k, v in policy_data.items()}

    return serializable

def create_grids(agent, usable_ace=False, starting_pos=12):
    """Create value and policy grid given an agent."""
    # convert our state-action values to state values
    # and build a policy dictionary that maps observations to actions
    state_value = defaultdict(float)
    policy = defaultdict(int)
    for obs, action_values in agent.q_values.items():
        state_value[obs] = action_values
        policy[obs] = action_values

    player_count, dealer_count = np.meshgrid(
        # players count, dealers face-up card
        np.arange(starting_pos, 22),
        np.arange(1, 11),
    )

    # create the value grid for plotting
    value = np.apply_along_axis(
        lambda obs: state_value[(obs[0], obs[1], usable_ace)],
        axis=2,
        arr=np.dstack([player_count, dealer_count]),
    )
    value_grid = player_count, dealer_count, value

    # create the policy grid for plotting
    policy_grid = np.apply_along_axis(
        lambda obs: policy[(obs[0], obs[1], usable_ace)],
        axis=2,
        arr=np.dstack([player_count, dealer_count]),
    )
    return value_grid, policy_grid
    