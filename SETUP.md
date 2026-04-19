# Kwamib profile repo — setup

This is your GitHub profile README repo. The repo name must match your username **exactly**: `Kwamib`.

## One-time setup

```bash
# 1. Create the repo on github.com
#    Name: Kwamib
#    Public, with a README (you'll overwrite it)

# 2. Clone it locally
git clone https://github.com/Kwamib/Kwamib.git
cd Kwamib

# 3. Drop in these three files:
#    - README.md
#    - 3d-skyline-config.json
#    - .github/workflows/profile-3d.yml

# 4. Commit and push
git add .
git commit -m "feat: profile README with 3D skyline"
git push
```

## What happens next

1. The push triggers the workflow immediately (thanks to `push` trigger on main).
2. The workflow runs `yoshi389111/github-profile-3d-contrib` against your contribution data.
3. It generates several SVG variants into `profile-3d-contrib/`:
   - `profile-night-rainbow.svg` ← the one referenced in the README
   - `profile-night-view.svg`, `profile-night-green.svg`, and others
4. It commits those SVGs back to the repo.
5. Your profile page at github.com/Kwamib now shows the skyline.
6. Every day at 00:00 UTC, the cron refreshes it.

## Picking a different skyline style

After the first run, browse `profile-3d-contrib/` in your repo. There are ~10 variants. Change the image path in README.md to whichever one you like best. Popular picks:

- `profile-night-rainbow.svg` — colorful buildings on dark
- `profile-night-view.svg` — green-on-dark, classic
- `profile-gitblock.svg` — Minecraft-style blocks
- `profile-season-animate.svg` — animated, seasonal colors

## Troubleshooting

**Workflow doesn't run on first push.** Check Actions tab → enable workflows. New repos sometimes have them disabled.

**Empty skyline.** Your contribution count is pulled from the GitHub GraphQL API via `GITHUB_TOKEN`. Private contributions need to be enabled on your profile (Settings → Profile → "Include private contributions").

**Want to trigger a refresh manually.** Actions tab → "Generate 3D contribution skyline" → Run workflow.
