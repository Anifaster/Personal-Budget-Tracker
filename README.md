# Personal Budget Tracker — Android edition
A Kivy port of Team C's original Python budget tracker. The original models, ledger, calculations and JSON storage are unchanged. The new interface supports income/expense recording, editing/deletion, filtering, balance, expense bars and monthly summaries. Currency label is KRW; use only one currency per ledger (no conversion). Data stays in app-private local storage. Uninstalling the app may erase it. No network or account is required for normal use. No automatic desktop data import or cloud sync is included.

## Build an APK using GitHub (Windows or any computer)
1. Extract this ZIP. Create a private GitHub repository at https://github.com/new with no initial files.
2. Upload the extracted files at the repository root, INCLUDING `.github/workflows/android.yml` (hidden folder). GitHub Desktop or git is recommended so the hidden folder is included. Commit and push to branch `main`.
3. Go to Actions > Build Android APK > Run workflow (if not started automatically). If Actions are disabled, enable them in repository settings.
4. Once the build succeeds, open that run and download `BudgetTracker-Android` under Artifacts. Extract the downloaded ZIP to obtain the APK.
5. Transfer the APK to your Android device. Open it in Files and allow installation from that source when prompted; switch that permission off afterward. This is a debug-signed personal-use build, not a Play Store release. Only install builds from your own trusted repository.

## Local build (Linux / WSL2)
Use the official Buildozer setup guide https://buildozer.readthedocs.io/en/latest/installation/ (Ubuntu 22.04, Java 17, Python 3.11 environment). Copy files into the Linux home directory, then execute `buildozer -v android debug`. APK output is in `bin/`. The first build downloads Android tooling. Build configurations may need changes if upstream tools change.

## Desktop preview and tests
`python -m pip install kivy==2.3.1`
`python main.py`
`python -m unittest test_budget -v`

## Verification status
Original financial tests and Python syntax checked locally. Android SDK, Kivy runtime and Buildozer are not installed in the delivery environment, so the mobile UI and APK build have not been executed or verified. This ZIP is source code, not an installable APK.
