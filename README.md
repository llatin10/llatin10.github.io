# llatin10.github.io (GitHub Pages)

This folder is the source for **https://llatin10.github.io/**.

## One-time setup on GitHub

1. Create a **new public** repository named exactly **`llatin10.github.io`** (Settings → must match your username).
2. Do **not** add a README or .gitignore on GitHub (keep the repo empty), or pull before first push.
3. In this folder, run:

```bash
cd "/Users/llatin/.cursor/HTML URL"
git remote add origin https://github.com/llatin10/llatin10.github.io.git
git branch -M main
git push -u origin main
```

4. On GitHub: **Settings → Pages** → Source: **Deploy from a branch** → Branch **main** → folder **/ (root)** → Save.

After a minute or two, the site is live at **https://llatin10.github.io/**.

## Adding or updating pages

1. Add or edit `.html` files in this folder.
2. Optionally add a link on `index.html` (or change the redirect) if you want a landing page listing all docs.
3. Commit and push:

```bash
cd "/Users/llatin/.cursor/HTML URL"
git add -A
git status
git commit -m "Update pages"
git push
```

Each file is at `https://llatin10.github.io/<filename>.html`.

## Notes

- `.nojekyll` disables Jekyll so static files are served as-is.
- Ask Cursor in this folder to update `index.html` when you add important new HTML pages you want linked from the home URL.
