# -*- coding: utf-8 -*-
"""Stock Allocation TD3 v2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1brdabNHZk5BqjV_peAhs7GLoP3L1IlX_
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import datetime as dt

from sklearn.preprocessing import StandardScaler

from google.colab import drive
drive.mount('/content/drive')

df = pd.read_csv('/content/drive/MyDrive/Part 3. AI and ML in Finance/Stocks_Data.csv')
df.set_index('Date',inplace=True)

scaler = StandardScaler()
scaler.fit(df.values)

class Stock_Environment():
  def __init__(self, action_dim, obs_dim, time_delta, window_length, df):
    self.init_cash = 1000
    self.time_delta = time_delta
    self.window_length = window_length

    self.action_dim = action_dim
    self.obs_dim = obs_dim

    self.df = df.copy()

    self.reset()

  def reset(self):
    # self.action = np.zeros(self.action_dim)
    # self.obs = np.zeros(self.obs_dim)
    self.done = False

    self.current_value = self.init_cash

    self.select_window()

    self.allocations_list = []

    self.reward = 0
    self.rewards_list = []

    return np.array(self.df_window.iloc[0])

  def select_window(self):
    max_windows = self.df.shape[0]-self.window_length-1
    window_start =  int(np.round(np.random.uniform(0,1)*max_windows))
    window_end  = window_start + self.window_length
    self.df_window = self.df.iloc[window_start:(window_end+1)]
    self.current_index = 0

  #allocate at today's close prices and analyze at 0+time_delta close prices
  #TCS, Reliance, HDFC Bank in that order
  def allocate(self,allocations):
    #Weight
    # for i in range(len(allocations)):
    #   if allocations[i] < 0:
    #     allocations[i] = 0
    # sum_allocation = sum(allocations)
    # for i in range(len(allocations)):
    #   if sum_allocation == 0:
    #     allocations[i] = 1/len(allocations)
    #   else:
    #     allocations[i] = allocations[i]/sum_allocation

    #Stock pick
    max_index = np.argmax(allocations)
    for i in range(len(allocations)):
      if i==max_index:
        allocations[i] = 1
      else:
        allocations[i] = 0


    self.allocations_list.append(allocations)

    previous_value = self.current_value
    
    prices_start = self.df_window.iloc[self.current_index][['TCS_Close','Reliance_Close','HDFCBank_Close']]
    self.current_index += self.time_delta
    prices_end = self.df_window.iloc[self.current_index][['TCS_Close','Reliance_Close','HDFCBank_Close']]
    period_return = prices_end/prices_start - 1
    portfolio_compound = 1 + allocations[0]*period_return[0] + allocations[1]*period_return[1] + allocations[2]*period_return[2] + allocations[3]*0
    self.current_value = self.current_value * portfolio_compound
    self.reward = self.current_value - previous_value
    self.rewards_list.append(self.reward)

    if self.current_index == self.window_length:
      self.done = True

    if (self.current_index + self.time_delta)>self.window_length:
      self.done = True

  def step(self, allocations):
    self.allocate(allocations)
    return np.array(self.df_window.iloc[self.current_index]),self.reward,self.done
    
  def sample(self):
    sample_allocations = np.random.uniform(0,1,self.action_dim)
  #Weights
    # if sum(sample_allocations)>1:
    #   sum_allocations = sum(sample_allocations)
    #   for i in range(len(sample_allocations)):
    #     sample_allocations[i] = sample_allocations[i]/sum_allocations

  #Pick stock
    max_index = np.argmax(sample_allocations)
    for i in range(len(sample_allocations)):
      if i==max_index:
        sample_allocations[i] = 1
      else:
        sample_allocations[i] = 0
    return np.array(sample_allocations)



action_dim, obs_dim, time_delta, window_length = 4,90,5,df.shape[0]-1
env = Stock_Environment(action_dim, obs_dim, time_delta, window_length,df)
env.reset()
while not env.done:
  # action = env.sample()
  action = [.6,.2,.2,.0]
  # print(action)
  next_state,reward,done = env.step(action)
  # print(f'reward : {reward} /t Current Index: {env.current_index} /t Current Value: {env.current_value}')
print(f'Total Reward: {sum(env.rewards_list)}')
# print(env.allocations_list)
# print(next_state)

class Actor(keras.Model):
  def __init__(self, state_dim, action_dim, max_action):
    super(Actor, self).__init__()
    self.layer_1 = keras.layers.Dense(state_dim, activation='relu', 
		                                  kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                    scale=1./3., distribution = 'uniform'))
    self.layer_2 = keras.layers.Dense(400, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))
    self.layer_3 = keras.layers.Dense(300, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))
    self.layer_4 = keras.layers.Dense(action_dim, activation='tanh',
		                                 kernel_initializer=tf.random_uniform_initializer(
		                                 	minval=-3e-3, maxval=3e-3))
    self.max_action = max_action

  def call(self, obs):
    x = self.layer_1(obs)
    x = self.layer_2(x)
    x = self.layer_3(x)
    x = self.layer_4(x)

	#Returns weights
    x = x * self.max_action
    return x
    
  #Pick STock
    # x = x[0].numpy()
    # max_index = np.argmax(x)
    # for i in range(len(x)):
    #   if i==max_index:
    #     x[i] = 1
    #   else:
    #     x[i] = 0
    # return tf.convert_to_tensor([x], dtype= tf.float32)

class Critic(keras.Model):
	def __init__(self, state_dim, action_dim):

		super(Critic, self).__init__()
		# The First Critic NN
		self.layer_1 = keras.layers.Dense(state_dim + action_dim, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))
		self.layer_2 = keras.layers.Dense(400, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))
		self.layer_3 = keras.layers.Dense(300, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))
		self.layer_4 = keras.layers.Dense(1, kernel_initializer=tf.random_uniform_initializer(
			minval=-3e-3, maxval=3e-3))
		# The Second Critic NN
		self.layer_5 = keras.layers.Dense(state_dim + action_dim, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))     
		self.layer_6 = keras.layers.Dense(400, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))
		self.layer_7 = keras.layers.Dense(300, activation='relu',
		                                 kernel_initializer=tf.keras.initializers.VarianceScaling(
		                                 	scale=1./3., distribution = 'uniform'))
		self.layer_8 = keras.layers.Dense(1, kernel_initializer=tf.random_uniform_initializer(
			minval=-3e-3, maxval=3e-3))

	def call(self, obs, actions):
		x0 = tf.concat([obs, actions], 1)
		# forward propagate the first NN
		x1 = self.layer_1(x0)
		x1 = self.layer_2(x1)
		x1 = self.layer_3(x1)
		x1 = self.layer_4(x1)
		# forward propagate the second NN
		x2 = self.layer_5(x0)
		x2 = self.layer_6(x2)
		x2 = self.layer_7(x2)
		x2 = self.layer_8(x2)        
		return x1, x2

	def Q1(self, state, action):
		x0 = tf.concat([state, action], 1)
		x1 = self.layer_1(x0)
		x1 = self.layer_2(x1)
		x1 = self.layer_3(x1)
		x1 = self.layer_4(x1)
		return x1

class ReplayBuffer(object):
    # The memory to store transitions as the agent plays the environment
    def __init__(self, max_size=1e6):
        self.storage = []
        self.max_size = max_size
        self.ptr = 0
        
    def add(self, transition):
        if len(self.storage) == self.max_size:
            self.storage[int(self.ptr)] = transition
            self.ptr = (self.ptr + 1) % self.max_size
        else:
            self.storage.append(transition)
            
    def sample(self, batch_size):
        ind = np.random.randint(0, len(self.storage),  size=batch_size)
        batch_states, batch_next_states, batch_actions, batch_rewards, batch_dones = [], [], [], [], []
        for i in ind:
            state, next_state, action, reward, done = self.storage[i]
            batch_states.append(np.array(state, copy=False))
            batch_next_states.append(np.array(next_state, copy=False))
            batch_actions.append(np.array(action, copy=False))
            batch_rewards.append(np.array(reward, copy=False))
            batch_dones.append(np.array(done, copy=False))
        return np.array(batch_states), np.array(batch_next_states), np.array(batch_actions), np.array(batch_rewards).reshape(-1, 1), np.array(batch_dones).reshape(-1, 1)

def Scale_Fit(a, transform=False):
  # print(a)
  if transform == True:
    return scaler.transform([a])[0]
  else:
    return a

class TD3(object):

  def __init__(self,state_dim,action_dim,max_action,current_time = None,summaries: bool = False,gamma = 0.99,tau = 0.005,noise_std = 0.2,noise_clip = 0.5,
                expl_noise = 1,actor_train_interval = 2,actor_lr = 3e-4,critic_lr = 3e-4,critic_loss_fn = None):

    self.actor = Actor(state_dim, action_dim, max_action)
    self.actor_target = Actor(state_dim, action_dim, max_action)
    for t, e in zip(self.actor_target.trainable_variables, self.actor.trainable_variables):
      t.assign(e)
    self.actor_optimizer = keras.optimizers.Adam(learning_rate=actor_lr)


    self.critic = Critic(state_dim, action_dim)
    self.critic_target = Critic(state_dim, action_dim)
    for t, e in zip(self.critic_target.trainable_variables, self.critic.trainable_variables):
      t.assign(e)
    self.critic_optimizer = keras.optimizers.Adam(learning_rate=actor_lr)
    if critic_loss_fn is not None:
      self.critic_loss_fn = critic_loss_fn
    else:
      self.critic_loss_fn = tf.keras.losses.Huber()

    self.action_dim = action_dim
    self.max_action = max_action
    self.gamma = gamma
    self.tau = tau
    self.noise_std = noise_std
    self.noise_clip = noise_clip
    self.expl_noise = expl_noise
    self.actor_train_interval = actor_train_interval
    self.summaries = summaries
    if current_time is None:
      self.current_time = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    else:
      self.current_time = current_time
    if self.summaries:
      self.train_writer = tf.summary.create_file_writer('./logs/' + self.current_time)

    self.train_it = 0

  def select_action(self, state, noise: bool = False):
		# Action selection by the actor_network.
    state = state.reshape(1, -1)
    action = self.actor.call(state)[0].numpy() #action = self.actor.call(state)[0].numpy()
    if noise:
      noise = tf.random.normal(action.shape, mean=0, stddev=self.expl_noise)
      action = tf.clip_by_value(action + noise, 0, self.max_action)
    return action

  def train(self, replay_buffer, batch_size=512):
		# training of the Actor and Critic networks.
    self.train_it += 1

		# create a sample of transitions
    batch_states, batch_next_states, batch_actions, batch_rewards, batch_dones = replay_buffer.sample(batch_size)

		# calculate a' and add noise
    next_actions = self.actor_target.call(batch_next_states)

    noise = tf.random.normal(batch_actions.shape, mean=0, stddev=self.noise_std)
    noise = tf.clip_by_value(noise, -self.noise_clip, self.noise_clip)
    noisy_next_actions = tf.clip_by_value(next_actions + noise, 0, self.max_action)

		# calculate the min(Q(s', a')) from the two critic target networks
    target_q1, target_q2 = self.critic_target.call(batch_next_states, noisy_next_actions)
    target_q = tf.minimum(target_q1, target_q2)

		# calculate the target Q(s, a)
    td_targets = tf.stop_gradient(batch_rewards + (1 - batch_dones) * self.gamma * target_q)

		# Use gradient descent on the critic network
    trainable_critic_variables = self.critic.trainable_variables

    with tf.GradientTape(watch_accessed_variables=False) as tape:
      tape.watch(trainable_critic_variables)
      model_q1, model_q2 = self.critic(batch_states, batch_actions)
      critic_loss = (self.critic_loss_fn(td_targets, model_q1) + self.critic_loss_fn(td_targets, model_q2))
    critic_grads = tape.gradient(critic_loss, trainable_critic_variables)
    self.critic_optimizer.apply_gradients(zip(critic_grads, trainable_critic_variables))

		# create tensorboard summaries
		# if self.summaries:
		# 	if self.train_it % 100 == 0:
		# 		td_error_1 = td_targets - model_q1
		# 		td_error_2 = td_targets - model_q2
		# 		with self.train_writer.as_default():
		# 			tf.summary.scalar('td_target_mean', tf.reduce_mean(td_targets), step = self.train_it)
		# 			tf.summary.scalar('td_target_max', tf.reduce_max(td_targets), step = self.train_it)
		# 			tf.summary.scalar('td_target_min', tf.reduce_min(td_targets), step = self.train_it)

		# 			tf.summary.scalar('pred_mean_1', tf.reduce_mean(model_q1), step = self.train_it)
		# 			tf.summary.scalar('pred_max_1', tf.reduce_max(model_q1), step = self.train_it)
		# 			tf.summary.scalar('pred_min_1', tf.reduce_min(model_q1), step = self.train_it)

		# 			tf.summary.scalar('pred_mean_2', tf.reduce_mean(model_q2), step = self.train_it)
		# 			tf.summary.scalar('pred_max_2', tf.reduce_max(model_q2), step = self.train_it)
		# 			tf.summary.scalar('pred_min_2', tf.reduce_min(model_q2), step = self.train_it)

		# 			tf.summary.scalar('td_error_mean_1', tf.reduce_mean(td_error_1), step = self.train_it)
		# 			tf.summary.scalar('td_error_mean_abs_1', tf.reduce_mean(tf.abs(td_error_1)), step = self.train_it)
		# 			tf.summary.scalar('td_error_max_1', tf.reduce_max(td_error_1), step = self.train_it)
		# 			tf.summary.scalar('td_error_min_1', tf.reduce_min(td_error_1), step = self.train_it)

		# 			tf.summary.scalar('td_error_mean_2', tf.reduce_mean(td_error_2), step = self.train_it)
		# 			tf.summary.scalar('td_error_mean_abs_2', tf.reduce_mean(tf.abs(td_error_2)), step = self.train_it)
		# 			tf.summary.scalar('td_error_max_2', tf.reduce_max(td_error_2), step = self.train_it)
		# 			tf.summary.scalar('td_error_min_2', tf.reduce_min(td_error_2), step = self.train_it)

		# 			tf.summary.histogram('td_targets_hist', td_targets, step = self.train_it)
		# 			tf.summary.histogram('td_error_hist_1', td_error_1, step = self.train_it)
		# 			tf.summary.histogram('td_error_hist_2', td_error_2, step = self.train_it)
		# 			tf.summary.histogram('pred_hist_1', model_q1, step = self.train_it)
		# 			tf.summary.histogram('pred_hist_2', model_q2, step = self.train_it)



		# Use gradient ascent on the actor network at a set interval
    if self.train_it % self.actor_train_interval == 0:
      trainable_actor_variables = self.actor.trainable_variables

      with tf.GradientTape(watch_accessed_variables=False) as tape:
        tape.watch(trainable_actor_variables)
        # print(self.actor(batch_states).shape)
        actor_loss = -tf.reduce_mean(self.critic.Q1(batch_states, self.actor(batch_states)))
      actor_grads = tape.gradient(actor_loss, trainable_actor_variables)
      self.actor_optimizer.apply_gradients(zip(actor_grads, trainable_actor_variables))

			# update the weights in the critic and actor target models
      for t, e in zip(self.critic_target.trainable_variables, self.critic.trainable_variables):
        t.assign(t * (1 - self.tau) + e * self.tau)

      for t, e in zip(self.actor_target.trainable_variables, self.actor.trainable_variables):
        t.assign(t * (1 - self.tau) + e * self.tau)

			# create tensorboard summaries
      if self.summaries:
        if self.train_it % 100 == 0:
          with self.train_writer.as_default():
            tf.summary.scalar('actor_loss', actor_loss, step = self.train_it)


  def save(self, steps):
		# Save the weights of all the models.
    self.actor.save_weights('./models/{}/actor_{}'.format(self.current_time, steps))
    self.actor_target.save_weights('./models/{}/actor_target_{}'.format(self.current_time, steps))

    self.critic.save_weights('./models/{}/critic_{}'.format(self.current_time, steps))
    self.critic_target.save_weights('./models/{}/critic_target_{}'.format(self.current_time, steps))

action_dim , obs_dim = 4,90
max_action = 1
time_delta, window_length = 5,(df.shape[0]-1)
# warmups = 2
# memory_size = 100000
tau = 0.05
# actor_update_steps = 2
# transform = True
# episodes = 200
# class Agent():
#   def __init__(self, action_dim, state_dim, batch_size = 100, actor_lr = 0.001, critic_lr = 0.001, memory_size = 100000,
#                gamma = 0.99, actor_update_steps = 2, warmups = 1000, tau = 0.005, policy_noise = 0.01, noise_clip = 0.5)
# tf.random.set_seed(336699)
# agent = Agent(action_dim,obs_dim,warmups=warmups,memory_size=memory_size,tau = tau, actor_update_steps=actor_update_steps,transform=transform)
# ep_reward = []
# total_avgr = []
# target = False

env = Stock_Environment(action_dim, obs_dim, time_delta, window_length,df)
# result_writer = tf.summary.create_file_writer('./logs/' + current_time)

def evaluate_policy(policy, eval_episodes=2):
	# during training the policy will be evaluated without noise
  avg_reward = 0.
  for _ in range(eval_episodes):
    state = env.reset()
    done = False
    while not done:
      action = policy.select_action(state)
      state, reward, done = env.step(action)
      avg_reward += reward
    print(f'Average Allocations:{np.array(env.allocations_list).mean(axis=0)}')
  avg_reward /= eval_episodes
  print ("---------------------------------------")
  print ("Average Reward over the Evaluation Step: %f" % (avg_reward))
  print ("---------------------------------------")
  return avg_reward


# initialise the replay buffer
memory = ReplayBuffer()
# initialise the policy
policy = TD3(obs_dim, action_dim, max_action, current_time=None, summaries=False)

max_timesteps = 2e6
start_timesteps = 1e4
total_timesteps = 0
eval_freq = 500
save_freq = 1e5
eval_counter = 0
episode_num = 0
episode_reward = 0
done = True

while total_timesteps < max_timesteps:

  if done:

		# print the results at the end of the episode
    if total_timesteps != 0:
      print('Episode: {}, Total Timesteps: {}, Episode Reward: {:.2f}'.format(
				episode_num,
				total_timesteps,
				episode_reward
				))
			# with result_writer.as_default():
			# 	tf.summary.scalar('total_reward', episode_reward, step = episode_num)

    if eval_counter > eval_freq:
      eval_counter %= eval_freq
      evaluate_policy(policy)

    state = env.reset()

    done = False
    episode_reward = 0
    episode_timesteps = 0
    episode_num += 1

	# the environment will play the initial episodes randomly
  if total_timesteps < start_timesteps:
    action = env.sample()
  else: # select an action from the actor network with noise
    action = policy.select_action(state, noise=True)

	# the agent plays the action
  # print(action)
  next_state, reward, done = env.step(np.array(action))

	# add to the total episode reward
  episode_reward += reward

	# check if the episode is done
  done_bool = float(done)

	# add to the memory buffer
  memory.add((state, next_state, action, reward, done_bool))

	# update the state, episode timestep and total timestep
  state = next_state
  episode_timesteps += 1
  total_timesteps += 1
  eval_counter += 1

	# train after the first episode
  if total_timesteps > start_timesteps:
    policy.train(memory)
    
    # save the model    
  if total_timesteps % save_freq == 0:
    policy.save(int(total_timesteps / save_freq))

import matplotlib.pyplot as plt
plt.plot(np.linspace(0,episodes-1,episodes), ep_reward, 'r', np.linspace(0,episodes-1,episodes), total_avgr, '--b')
plt.show()

# actor = tf.keras.models.load_model('/content/drive/MyDrive/Part 3. AI and ML in Finance/Stock_allocation_actor')
# actor = agent.actor
env = Stock_Environment(action_dim, obs_dim, 5, df.shape[0]-1,df)
state = env.reset()
row = 0
allocations_list = []
total_reward = 0
while not env.done:
  state = Scale_Fit(state,transform)
  state = tf.convert_to_tensor([state], dtype=tf.float32)
  allocation = agent.actor.forward(state)[0]
  allocations_list.append(np.array(allocation))
  next_state, reward, done = env.action(np.array(allocation))
  total_reward += reward
  state = next_state
  # print(f'Current index:{env.current_index} out of {df.shape[0]}')

print(f'Total Reward: {sum(env.rewards_list)} and also {total_reward}')
print(f'Portfolio Returns: {np.round(env.current_value/env.init_cash - 1,4)*100}%')
print(env.allocations_list)

import plotly.express as px
Allocations = pd.DataFrame(env.allocations_list.reshape(-1,1),
                           np.tile(['TCS','Reliance','HDFC Bank','Cash'],env.allocations_list.shape[0]),
                           df.index,columns=['Allocation','Stock','Date'])

fig = px.area(Allocations, x='Date', y='Allocation',
            color="Stock",
            hover_data=['Date'])
 
fig.show()

agent.memory.action_memory[:1000]
# agent.actor.forward(tf.convert_to_tensor([env.reset()], dtype=tf.float32))

memory.storage[0][2]

a = [[1,2,3,4],[5,6,7,8]]
np.array(a).mean(axis=0)

tf.convert_to_tensor(
    [[1,2,3,4]], dtype=None, dtype_hint=None, name=None
)

