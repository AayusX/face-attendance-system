# Microsoft Store — Partner Center Checklist

Follow this order. Only steps 1–2 are long; the rest is form-filling.

## Step 0 — Preflight (do these once)
- [ ] Confirm the app **runs from the MSIX** (already verified locally: it writes data
      to `%LOCALAPPDATA%\...\FaceAttendanceSystem`).
- [ ] Host the privacy policy. Easiest free option (repo is already pushed to GitHub):
      1. In your browser: repo **Settings → Pages → Source: Deploy from a branch → main /
         (root) → Save**.
      2. Wait ~1 min. Your policy URL will be:
         `https://AayusX.github.io/face-attendance-system/store/PRIVACY_POLICY.html`
      (GitHub renders the `.md` in `store/` automatically.)
- [ ] Take screenshots — done automatically into `store/screenshots/*.png`
      (re-run anytime with `python main.py --capture-shots store\screenshots`).

## Step 1 — Developer account for free (your VS Enterprise benefit)
1. Go to https://partner.microsoft.com → **Sign up** → Microsoft Partner Network →
   "Microsoft Store for apps" / Windows developer account.
2. **Key free path:** sign in with the Microsoft account linked to your Visual
   Studio Enterprise subscription (activate it at https://my.visualstudio.com
   using your GitHub Student Pack benefit first).
3. When asked about the developer account fee: Visual Studio Enterprise
   subscribers qualify for a **free** individual Store developer account
   (normally $19/individual, $99/company). If you don't see the free option,
   accept the standard one and contact support after — or double-check the
   subscription benefit page.
4. You'll also need a free **Microsoft Entra ID (Azure AD)** tenant — the sign-up
   flow offers to create one. Resolve the "organisation domain" prompt with a
   personal domain (e.g. yourname.onmicrosoft.com).
5. Set your **publisher display name** (shown to users, e.g. "Aayush Bhandari").

## Step 2 — Create the app + reserve identity
1. Partner Center → **Windows and Xbox** → **Applications** → **Create new product** →
   pick **"Desktop application"** (NOT MSI, because we are submitting an MSIX).
2. Reserve the app name **"Face Attendance System"**.
3. Info you can now read off the app page (you'll need this next):
   - **Publisher ID** (a long GUID or `CN=...`) → your `-Publisher` value
   - The package family / identity your listing will use

## Step 3 — Rebuild the MSIX with your real publisher, then upload
Run (powershell, from the repo root):
```
powershell -File msix\make_msix.ps1 -Publisher "CN=<YOUR_PUBLISHER_ID>"
```
(no `-SelfSign` — for Store submissions **Microsoft re-signs the package**; keep the
self-signed copy only for internal testing). This produces
`msix\FaceAttendanceSystem_<version>_x64.msix`.

1. In the submission, go to **Packages** → **Upload** → choose that `.msix`.
2. Wait for package validation to finish (it runs the app in a VM briefly).

## Step 4 — Listing details (use STORE_LISTING.md)
- Product overview: short + long description, keywords, category **Education**.
- **Websites:** add the GitHub repo.
- **Privacy policy URL:** your hosted page from Step 0.
- **Declarations → Capabilities:** ensure "webcam" is declared (it is, in the
      AppxManifest).
- **Age ratings** questionnaire: answer no to most; data is stored locally.
      Camera use = declare under "sharing info" only if applicable. Mark
      "Does not collect personal information".
- **Package type:** Desktop app / full trust.

## Step 5 — Screenshots, logos, release notes
- Upload screenshots (Step 0), Store logo 300x300 (`msix_assets/app300.png`), and
  the release notes text from STORE_LISTING.md.

## Step 6 — Submit
- Click **Submit to Store** → moves to certification (typically ~1–3 days).
- If certification fails: read the failure detail, fix, resubmit (packaging you
  can regenerate with `make_msix.ps1` at any time; bump `-Version` on update).

## Useful commands
```
# re-pack from a fresh build (after build_windows.bat):
powershell -File msix\make_msix.ps1 -Publisher "CN=<id>"

# local install test (self-signed):
powershell -File msix\make_msix.ps1 -SelfSign
Add-AppxPackage -Path msix\FaceAttendanceSystem_1.0.0.0_x64.msix

# remove the package:
Get-AppxPackage *FaceAttendance* | Remove-AppxPackage
```