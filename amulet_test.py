import amulet
from amulet.api.block import Block

world = amulet.load_level("/home/tom/.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances/26.1/minecraft/saves/Wool Drive")

red = Block("minecraft", "red_wool")

world.set_version_block(
    0, -60, 0,
    "minecraft:overworld",
    ("java", (1, 20, 4)),
    red,
)

world.save()
world.close()
print("Red wool Placed")