# %%
from imgen import gen_image
from PIL import Image
from math import sqrt
import random
from copy import deepcopy

#%%
# Temp optimization goal: find bluest image!
def square(rgb, size=(100, 100)):
    return Image.new("RGB", size, rgb)

def dominant_color(img):
    return img.copy() \
        .resize((1, 1), resample=0) \
        .getpixel((0, 0))

def rgb_distance(c1, c2):
    return sqrt(sum(map(lambda x: (x[1]-x[0])**2, zip(c1, c2))))

def score(img):
    # Dummy scoring for how blue an image is
    return rgb_distance(dominant_color(img), (0, 0, 255))

#%%
# Temp prompt engineering
def load_words(filename):
    return open(filename).read().split()

wordlists = [
    load_words("wordlists/adjectives.txt"),
    load_words("wordlists/nouns.txt"),
    load_words("wordlists/artstyles.txt")
]

#%%
class Prompt:
    score = 0
    img = None
    def __init__(self, adjective, noun, artstyle):
        self._words = [adjective, noun, artstyle]

    def modify(self, field):
        self._words[field] = random.choice(wordlists[field])

    def __str__(self):
        return f"{self._words[0]} {self._words[1]} {self._words[2]} painting"

# %%
def mcmc(prompt):
    # Set timers
    t = 0
    tmax = 10
    attempts = 10
    img = gen_image(prompt)
    scores = [score(img)]

    while t < tmax and attempts > 0:
        attempts -= 1

        # Get new prompt and score generated image
        new_prompt = deepcopy(prompt)
        new_prompt.modify(field=random.randint(0, 2))
        new_img = gen_image(new_prompt)
        new_score = score(new_img)

        if new_score < scores[-1]:
            prompt = new_prompt
            scores.append(new_score)

            # Update MCMC steps and reset attempts
            t += 1
            attempts = 10

            # Check progress
            print(prompt, " ", new_score)
            display(new_img)

    return scores, new_prompt, new_img


# %%
scores, prompt, img = mcmc(Prompt("ninja", "turtle", "renaissance"))