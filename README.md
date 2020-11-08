# CraftingTable

Put Minecraft on the crafting table!

*CraftingTable* is a Python toolchain to deobfuscate and decompile Minecraft servers to Java source code, and recompile and repack it from modified source code. It effectively allows Minecraft to be modified on a Java level.

The scripts are written with automation in mind, with an example use case being to keep mods up to the latest Minecraft snapshot, which is a huge limitation to modded servers like CraftBukkit. However, *CraftingTable* doses not provide any modding API. It could be used to write one, but it is only meant to provide access to the Minecraft server source code as well as means to recompile it into a modded server.

At its core, *CraftingTable* makes use of these components:

* [MC-Remapper](https://github.com/HeartPattern/MC-Remapper), a tool for deobfuscating Minecraft servers using Mojang's obfuscation maps,
* [fernflower](https://github.com/fesh0r/fernflower), a pretty darn good Java decompiler, and
* `javac`, the Java compiler (JDK 8).

## Requirements

*CraftingTable* requires git for setting up, as well as a JDK 8 (newer versions can be used, but may not recompile correctly, since Minecraft is written in Java 8).

## Usage

The *CraftingTable* workflow consists of two steps, *unpacking* and *packing*.

### Unpack

The unpack step deobfuscates and decompiles the Minecraft server. The `unpack.py` script is used as follows:

```
unpack.py <jar> <obf> <out>
```

In the above, `<jar>` is the path to the server jar, `<obf>` the path to the obfuscation map and `<out>` the output directory.

Unpacking may take a while. Once done, the output directory contains

* a `remap.jar` file containing the deobfuscated Minecraft server,
* a folder `src` containing the decompiled Java sources and
* a `json` file containing some information about the unpacked jar that will be needed when packing.

#### Setup

When started for the first time, a setup is run before unpacking, building *MC-Remapper* and *fernflower* on your system, which may take a bit. For this, you must have `git` and a JDK installed on your system.

You don't have to start this manually, as it is automatically run each time you use the `unpack.py` scripts

### Pack

The pack step compiles the modified Java sources and creates a modified Minecraft server jar. It does *not* obfuscate the Minecraft server again, as that is typically not needed. The `pack.py` script is used as follows:

```
pack.py <remap> <json>
```

Here, `<remap>` is the deobfuscated server jar file (`remap.jar`) and `<json>` the JSON file produced by the unpacking process.

The script detects which Java sources have been modified and tries to compile them. For this, the `javac` must be locatable via the `PATH` variable and is expected to be JDK 8. The result is a repacked Minecraft server jar that you can use like the original Minecraft server.

## Decompiler Limitations

Java Decompilers aren't perfect. In fact, some things cannot be decompiled properly from JVM bytecode. This means that not *all* decompiled code can be recompiled as is. In these cases, manual fixes are necessary, which may require advanced Java knowledge.

This section covers some pitfalls you may encounter.

### Erased Generic Type Parameters

The JVM performs type erasure during compilation, which cannot be perfectly undone. In these cases, local variables with types that take generic type parameters will be decompiled without any type parameters. For example, a `List<Something>` may end up as a just `List`, which will result in failed type checks when trying to recompile.

The generic type parameters have to be restored manually, which can usually be done by analyzing the compiler's error message and the variable context to figure out what the generic parameter should be.

### Missing Typecasts

For similar reasons, some typecasts of the original source code may no longer be there after decompilation, resulting in failed type checks just like above. These have to be manually restored in similar fashion.

### Integer Lists

I have observed at least one case where Minecraft code uses a `List<Integer>`, which can result in a very tricky edge case related to the `remove` function.

The decompiler may produce a line such as this:

```java
list.remove(i)
```

When `i` was an `Integer` in the original source code, we have an ambiguity problem after decompilation:

* `remove(int)` interprets `i` as the *index* of the item to remove.
* `remove(Integer)` interprets `i` as the *value* of the item to remove.

The code produced by the decompiler will always use the index variant, because the boxing typecast to `Integer` is *not* being decompiled if it was there. It recompiles just fine, because `remove(int)` does work. However, the semantics are wrong, and the cast to `Integer` has to be manually restored.

There is no way to detect this other than the server probably crashing seemingly at random, which may not be easy to reproduce. To avoid it, have a very close look at all usages of `remove` if you spot an `Integer` list.