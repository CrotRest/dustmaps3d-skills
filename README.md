# dustmaps3d-skills

[中文](#中文) | [English](#english)

Agent skills (Claude Code and compatible agents) for the all-sky 3D dust extinction map of Wang et al. (2025), built from Gaia and LAMOST — the same four features as the 3D Dust Map website.

| skill | what it does | runs on |
| --- | --- | --- |
| [`dust-extinction-query`](skills/dust-extinction-query) | E(B−V), dust density, uncertainty and maximum reliable distance for a sightline or a CSV/FITS catalogue; reddening coefficients (Zhang et al. 2024 / 2023) | your machine (`pip install dustmaps3d`) |
| [`dust-sky-map`](skills/dust-sky-map) | Cartesian or orthographic maps of the mean dust density in a distance shell | a [dustmaps3d-backend](https://github.com/SunnyHina/dustmaps3d-backend) server |
| [`dust-bubble-plot`](skills/dust-bubble-plot) | near / middle / far three-panel bubble figures plus the inner-disk vs annulus density analysis | a dustmaps3d-backend server |
| [`astro-coord-tools`](skills/astro-coord-tools) | ICRS / Galactic / ecliptic / heliocentric XYZ conversion; angular ↔ physical size | your machine (`astropy`) |

## 中文

### 安装

把下面这段话发给你的 AI 助手（Claude Code 等），它会从本仓库安装全部四个 Skill：

```text
请从 GitHub 仓库 https://github.com/CrotRest/dustmaps3d-skills 安装其中 skills/ 下的全部四个 Skill（dust-extinction-query、dust-sky-map、dust-bubble-plot、astro-coord-tools）：把每个文件夹完整复制到 ~/.claude/skills/ 下的同名目录（已存在就覆盖更新），然后读一遍各自的 SKILL.md，告诉我它们分别能做什么、需要先安装哪些依赖。
```

只装一个时，把文件夹名换成对应的那个。也可以手动安装：

```bash
git clone https://github.com/CrotRest/dustmaps3d-skills.git
cp -R dustmaps3d-skills/skills/* ~/.claude/skills/
```

### 依赖

- `dust-extinction-query`：`pip install dustmaps3d`；首次调用会自动下载约 400 MB 数据（国内优先 NADC 镜像）。红化系数另需 `xp-extinction-toolkit==1.0`（要求 `scipy<1.14`）或 `extinction-coefficient==1.8`。
- `dust-sky-map`、`dust-bubble-plot`：需要一个能访问的 dustmaps3d-backend 服务，地址用环境变量 `DUSTMAPS_API` 指定（默认 `http://127.0.0.1:58123`）。脚本只用 Python 标准库；三联图拼接可选 Pillow。
- `astro-coord-tools`：`astropy`（星表批量另需 `pandas`）。

## English

### Install

Send this to your AI assistant (Claude Code or similar) to install all four skills from this repository:

```text
Install all four skills under skills/ in the GitHub repository https://github.com/CrotRest/dustmaps3d-skills (dust-extinction-query, dust-sky-map, dust-bubble-plot, astro-coord-tools): copy each folder in full to a directory of the same name under ~/.claude/skills/ (overwrite to update if it exists), then read each SKILL.md and tell me what they do and which dependencies to install first.
```

For a single skill, name just that folder. Manual install:

```bash
git clone https://github.com/CrotRest/dustmaps3d-skills.git
cp -R dustmaps3d-skills/skills/* ~/.claude/skills/
```

### Requirements

- `dust-extinction-query`: `pip install dustmaps3d`; the first call downloads ~400 MB of data. Reddening coefficients additionally need `xp-extinction-toolkit==1.0` (with `scipy<1.14`) or `extinction-coefficient==1.8`.
- `dust-sky-map`, `dust-bubble-plot`: a reachable dustmaps3d-backend, set with `DUSTMAPS_API` (default `http://127.0.0.1:58123`). Standard library only; Pillow is optional for joining the three panels.
- `astro-coord-tools`: `astropy` (plus `pandas` for catalogues).

## Citation

- Wang, T. et al. (2025), An all-sky 3D dust map based on Gaia and LAMOST, ApJS 280, 15, [doi:10.3847/1538-4365/adea39](https://doi.org/10.3847/1538-4365/adea39)
- dustmaps3d: A Python package for easy access to the 3D dust map, [doi:10.12149/101619](https://doi.org/10.12149/101619)
- Zhang et al. (2024), ApJ 972, 207 / Zhang et al. (2023), ApJS 264, 14 — when their reddening coefficients are used

## License

MIT — see [LICENSE](LICENSE). The dust map data and the `dustmaps3d` package are distributed by their authors under their own terms.
