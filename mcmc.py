# %%
from imgen import gen_image
import random
from copy import deepcopy
from numpy import ones, exp, expand_dims
from IPython.display import display

# Quickly buffer image
gen_image("Testing bunny")

#%%
# Loading our pre-trained model for paintings prices
import autokeras as ak # We need this otherwise model doesn't load :(
from keras.models import load_model
price_model = load_model("model-full128_trainlong.h5", compile=False)

#%%
IMG_INPUT_SIZE = (128, 128)
def score(img):
    prediction = price_model.predict(expand_dims(img.resize(IMG_INPUT_SIZE), axis=0))
    # Values are log normalized
    return exp(prediction).item(0)

#%%
# Temp prompt engineering
def load_words(filename):
    return open(filename).read().splitlines()

def random_word_index(wordlist):
    return random.choices(range(len(wordlist)), weights=wordlist.weights)[0]

class Wordlist:
    def __init__(self, filename, reward):
        self.words = load_words(filename)
        self._rewards = reward
        self.reset_scores()

    def at(self, index):
        return self.words[index], self.weights[index]

    def reward(self, index, award_type):
        self.weights[index] += self._rewards[award_type]

    def __len__(self):
        return len(self.words)

    def reset_scores(self):
        self.weights = ones(len(self.words))

wordlists = [
    Wordlist("wordlists/adjectives.txt", reward=dict(small=10, big=100)),
    Wordlist("wordlists/nouns.txt", reward=dict(small=10, big=100)),
    Wordlist("wordlists/artstyles.txt", reward=dict(small=0, big=0.1))
]

#%%
class Prompt:
    score = 0
    img = None
    _last_mod_field = None
    def __init__(self, *wordlist_indices):
        self._word_indices = list(wordlist_indices)

    def modify(self, field):
        self._last_mod_field = field
        self._word_indices[field] = random_word_index(wordlists[field])

    def reward(self, reward_type):
        for field, i in enumerate(self._word_indices):
            wordlists[field].reward(i, reward_type)

    def reward_last_change(self, reward_type):
        i = self._last_mod_field
        wordlists[i].reward(self._word_indices[i], reward_type)

    def __str__(self):
        return " ".join((wordlist.words[index]
            for wordlist, index in zip(wordlists, self._word_indices))) \
                + " painting"

# %%
def mcmc(prompt, n=100, tries=10):
    # Set timers
    t = 0
    tmax = n
    attempts = tries

    # Initialize scores
    img = gen_image(prompt)
    score0 = score(img)
    scores = [score0]
    checkpoints = [score0]

    # Quick check
    with open("log/data.dat", "a") as f:
        f.write(f"{prompt}, {score0}\n")
    img.save(f"log/imgs/{len(scores)}.jpg")

    # Bias for initial guess
    for w in wordlists: w.reset_scores()
    prompt.reward("small")

    while t < tmax and attempts > 0:
        attempts -= 1

        # Get new prompt and score generated image
        new_prompt = deepcopy(prompt)
        field = random.randint(0, 2)
        new_prompt.modify(field)
        new_img = gen_image(new_prompt)
        new_score = score(new_img)
        scores.append(new_score)

        if new_score > checkpoints[-1]:
            # Last change is good! Reward!
            new_prompt.reward_last_change("big")

            # Save new prompt
            prompt = new_prompt
            img = new_img
            checkpoints.append(new_score)

            # Update MCMC steps and reset attempts
            t += 1
            attempts = tries

            # Check progress
            # print(prompt, " ", new_score)
            # display(new_img)
            with open("log/data.dat", "a") as f:
                f.write(f"{prompt}, {new_score}\n")
            img.save(f"log/imgs/{len(scores)}.jpg")

        else:
            # Hard to beat prompt
            prompt.reward("small")

    return scores, checkpoints, prompt, img


# %%
output = mcmc(Prompt(0, 0, 1), n=100, tries=100)
print("Done!")