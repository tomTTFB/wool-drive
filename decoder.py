import amulet

world = "/home/tom/.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances/26.1/minecraft/saves/Wool Drive"
level = amulet.load_level(world)

for x in range(54):
    block, _ = level.get_version_block(x, -60, 0, "minecraft:overworld", ("java", (1, 20, 4)))
    print(x, block.base_name)

level.close()