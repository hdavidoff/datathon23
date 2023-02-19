#%%
import torch
from diffusers import StableDiffusionPipeline

#%%
torch.cuda.empty_cache()
pipe = StableDiffusionPipeline.from_pretrained("./stable-diffusion-v1-5", torch_dtype=torch.float16)
pipe = pipe.to("cuda")

#%%
def gen_image(prompt, width=400, height=400, guidance=8.5, steps=20):
    return pipe(str(prompt), height=height, width=width,
        guidance_scale=guidance, num_inference_steps=steps).images[0]

#%%
# Test image generation
# img = gen_image("fox drinking honey impressionist painting")
# img

