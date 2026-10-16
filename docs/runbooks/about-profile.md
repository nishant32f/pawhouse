# Publish the About profile

Run this only after the user asks to merge and publish. Merging into `main` triggers GitHub Pages.

The website is `/Users/skypawalker/Dev/pawhouse` on Pluto. Its authoritative source is `/Users/skypawalker/Dropbox/Obsidian/public`.

1. Inspect the current Pluto branch, dirty files and vault revisions. Preserve other sessions' daily-publishing work. Coordinate publication before changing either source file.
2. Back up vault `index.md` and any existing `about.md` outside the public vault. Save the backups under a private dated directory.
3. Copy this reviewed branch's `content/about.md` to vault `public/about.md`. Reuse the existing `public/ascii-art.png`.
4. Apply only this branch's homepage biography and About-link changes to vault `public/index.md`. Compare with the current file and preserve any newer edits.
5. Rehearse `scripts/sync-content-from-vault.sh` using a disposable destination and state folder. Set `PUBLISH_REPO`, `PUBLISH_VAULT_PUBLIC` and `PUBLISH_STATE_DIR` explicitly. Confirm `about.md`, the discovery link and portrait survive.
6. Merge the approved PR only after the vault agrees with the reviewed profile. Do not switch or reset another session's checkout.
7. Watch the Pages workflow finish. Open `https://nishantkhurana.me/about` in a browser. Check portrait, search, theme toggle, garden navigation and Back/Forward from a nested note.
8. Verify `/about.html`, native metadata, social image and sitemap on the live site. Record the deployed commit and browser result.

Future edits belong in vault `public/about.md`. Publish through the existing notes workflow after inspecting its staging scope. The publish script stages every repository change.

If publication must be reversed, restore the two backed-up vault files and revert the profile commit through a reviewed branch. Rebuild and verify the garden. Removing only repository content will not persist through the next vault sync.
