import torch
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained("ostris/OpenFLUX.1", dtype=torch.bfloat16, device_map="cuda")

prompt = "Astronaut in a jungle, cold color palette, muted colors, detailed, 8k"
image = pipe(prompt).images[0]

image.save("astronaut_jungle.png")