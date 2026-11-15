import amulet
from amulet.api.block import Block
from amulet.api.block_entity import BlockEntity
from amulet_nbt import CompoundTag, ListTag, StringTag, ByteTag, NamedTag

world = "/home/tom/.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances/26.1/minecraft/saves/Wool Drive"
version = ("java", (1, 20, 4))
dim = "minecraft:overworld"

def side(lines):
    return CompoundTag({
        "messages": ListTag([StringTag(f'{{"text":"{l}"}}') for l in lines]),
        "color": StringTag("black"),
        "has_glowing_text": ByteTag(0),
    })

x, y, z = -1, -60, 0
nbt = NamedTag(CompoundTag({
    "front_text": side(["Wool Drive", "sigma.png", "194620 bytes", "walls 0-23"]),
    "back_text": side(["", "", "", ""]),
    "is_waxed": ByteTag(1),
}))

sign = Block("minecraft", "oak_sign", {"rotation": StringTag("4")})
entity = BlockEntity("minecraft", "sign", x, y, z, nbt)

level = amulet.load_level(world)
level.set_version_block(x, y, z, dim, version, sign, entity)
level.save()
level.close()
print("sign placed")