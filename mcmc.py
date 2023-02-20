# %%
from imgen import gen_image
from PIL import Image
import random
from copy import deepcopy
from numpy import ones, sqrt

#%%
# Temp optimization goal: find bluest image!
def square(rgb, size=(100, 100)):
    return Image.new("RGB", size, rgb)

# def dominant_color(img):
#     return img.copy() \
#         .resize((1, 1), resample=0) \
#         .getpixel((0, 0))

# def dominant_colors(img, palette_size=10, n=3):
#     # Resize image to speed up processing
#     clusters = img.copy() \
#         .resize((100, 100)) \
#         .convert("P", colors=palette_size)

#     color_counts = sorted(clusters.getcolors(), reverse=True)
#     palette = clusters.getpalette()
#     return [tuple(palette[c[1]*3:c[1]*3+3]) for c in color_counts[:n]]

def rgb_distance(c1, c2):
    # return sum(map(lambda x: (x[1]-x[0])**2, zip(c1, c2)))
    # Account a bit for human perception
    return 0.30 * (c2[0] - c1[0])**2 \
         + 0.59 * (c2[1] - c1[1])**2 \
         + 0.11 * (c2[2] - c1[2])**2

RED = (255, 30, 30)
GREEN = (30, 255, 30)
BLUE = (30, 30, 255)

def score(img):
    # Dummy scoring for how blue an image is
    return sum((rgb_distance(c, RED)
        for c in img.copy().resize((20, 20)).getdata()))

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
    Wordlist("wordlists/nouns.txt", reward=dict(small=20, big=200)),
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
def mcmc(prompt):
    # Set timers
    t = 0
    tmax = 10
    attempts = 10

    # Initialize scores
    img = gen_image(prompt)
    score0 = score(img)
    scores = [score0]
    checkpoints = [score0]

    # Quick check
    print(prompt, " ", score0)
    display(img)

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

        if new_score < checkpoints[-1]:
            # Last change is good! Reward!
            new_prompt.reward_last_change("big")

            # Save new prompt
            prompt = new_prompt
            img = new_img
            checkpoints.append(new_score)

            # Update MCMC steps and reset attempts
            t += 1
            attempts = 10

            # Check progress
            print(prompt, " ", new_score)
            display(new_img)

        else:
            # Hard to beat prompt
            prompt.reward("small")

    return scores, checkpoints, prompt, img


# %%
output = mcmc(Prompt(0, 0, 6))