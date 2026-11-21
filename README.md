# Velmaris

[![Competition](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![Rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/jembot21/velmaris-poster/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![Reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/jembot21/velmaris-poster/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

A program that draws a vintage travel poster for **Velmaris**, an invented tidal-island lighthouse republic. Created for the make.fun bounty **“The Poster for a Place That Isn't There.”**

Golden-hour light falls across a striped lighthouse and its keeper's cottage. A winding stone causeway emerges at low tide, crossing wet sand and reflective tidal pools; a beached rowing boat rests in the foreground. Layered colour, fine sea marks, a restrained indexed palette, and paper grain give the image the feel of a weathered travel lithograph. The place name, **VELMARIS**, is the only lettering in the poster.

The scene is drawn procedurally in Python with Pillow and the bundled fonts. A fixed random seed makes the textures repeatable. Rendering uses no network access or downloaded assets.

## Run

From the repository directory:

```sh
python3 main.py
```

The default output is `/output/entry.png`. The program creates the parent directory if needed; the destination must be writable. To choose a local destination:

```sh
VELMARIS_OUTPUT=./output/entry.png python3 main.py
```

The output is a **1024 × 1024 PNG**, limited to **1,048,576 bytes**. The program prints the destination, dimensions, and file size, and raises an error if the size cap is exceeded.

If Pillow is already installed, the program uses it. Otherwise it extracts the wheel in `vendor/` into a temporary directory and imports Pillow from there, without contacting a package registry. The bundled wheel targets **CPython 3.13 on Linux x86-64 with glibc 2.27 or newer**. Use that environment for the bundled fallback, or provide a compatible Pillow installation for another Python/platform combination. The fonts are loaded relative to `main.py`, so they do not depend on system fonts. For byte-identical renders across runs, keep the Python, Pillow, and bundled font versions the same.

## License

See [LICENSE](LICENSE).
